"""
api.py
JSON REST API for the React frontend. Reuses the same parsers, rule engine,
NLP classifier and PDF generator as app.py — only the transport layer changes
(JSON responses instead of server-rendered HTML).

Run: pip install -r requirements.txt && python api.py
Serves on http://127.0.0.1:5000, CORS-enabled for the Vite dev server (5173).
"""
import io
import os
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from models import Device
from parsers.detect import detect_and_parse
from rule_engine import evaluate
from nlp_classifier import classify_line, confirm_mapping, all_learned_mappings
from report_generator import generate_pdf

app = Flask(__name__)
CORS(app)

DEVICES: dict[str, Device] = {}
PENDING: list[dict] = []

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_configs")

CATEGORIES = [
    {"field": "session_timeout_set", "value": True, "label": "Session Timeout (Authentication / Session Security)"},
    {"field": "ssh_version", "value": 2, "label": "SSH Configuration"},
    {"field": "http_enabled", "value": True, "label": "HTTP Management Interface"},
    {"field": "logging_enabled", "value": True, "label": "Logging / Audit"},
    {"field": "telnet_enabled", "value": True, "label": "Telnet Access"},
    {"field": "ntp_configured", "value": True, "label": "Time Synchronization (NTP)"},
    {"field": "aaa_configured", "value": True, "label": "AAA / Centralized Authentication"},
    {"field": "snmp_detected", "value": True, "label": "SNMP"},
]


def device_summary(d: Device):
    return {"id": d.id, "filename": d.filename, "vendor": d.vendor,
            "hostname": d.cdm.hostname, "os": d.cdm.os, "score": d.score}


def device_detail(d: Device):
    return {
        **device_summary(d),
        "serial": d.cdm.serial,
        "findings": [
            {"rule_id": f.rule_id, "title": f.title, "framework": f.framework,
             "severity": f.severity, "passed": f.passed, "why": f.why,
             "remediation": f.remediation}
            for f in d.findings
        ],
    }


@app.route("/api/samples")
def list_samples():
    if not os.path.exists(SAMPLE_DIR):
        return jsonify([])
    return jsonify(sorted(os.listdir(SAMPLE_DIR)))


@app.route("/api/dashboard")
def dashboard_stats():
    devices = list(DEVICES.values())
    sev = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for d in devices:
        for f in d.findings:
            if not f.passed:
                sev[f.severity] += 1
    return jsonify({
        "total": len(devices),
        "compliant": sum(1 for d in devices if d.score == 100),
        "severity": sev,
        "devices": [device_summary(d) for d in devices],
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    body = request.get_json(force=True)
    sample = body.get("sample")
    if sample:
        with open(os.path.join(SAMPLE_DIR, sample)) as f:
            text = f.read()
        filename = sample
    else:
        text = body.get("config_text", "")
        filename = body.get("filename", "pasted-config.txt")

    if not text.strip():
        return jsonify({"error": "empty config"}), 400

    vendor, cdm, unrecognized = detect_and_parse(text)
    device_id = str(uuid.uuid4())[:8]
    findings = evaluate(cdm, vendor)
    device = Device(id=device_id, filename=filename, vendor=vendor, cdm=cdm,
                     findings=findings, raw_config=text)
    DEVICES[device_id] = device

    for line in unrecognized:
        suggestion = classify_line(line)
        if suggestion and suggestion.get("auto"):
            setattr(cdm, suggestion["field"], suggestion["value"])
            device.findings = evaluate(cdm, vendor)
        else:
            PENDING.append({"device_id": device_id, "line": line, "suggestion": suggestion})

    return jsonify(device_detail(device))


@app.route("/api/devices/<device_id>")
def get_device(device_id):
    d = DEVICES.get(device_id)
    if not d:
        return jsonify({"error": "not found"}), 404
    return jsonify(device_detail(d))


@app.route("/api/devices/<device_id>/pdf")
def get_pdf(device_id):
    d = DEVICES.get(device_id)
    if not d:
        return jsonify({"error": "not found"}), 404
    pdf = io.BytesIO()
    generate_pdf(d, pdf)
    pdf.seek(0)
    filename = secure_filename(f"{d.cdm.hostname}-report.pdf") or "netcomply-report.pdf"
    return send_file(pdf, mimetype="application/pdf", as_attachment=True,
                     download_name=filename)


@app.route("/api/training/pending")
def get_pending():
    return jsonify({"pending": PENDING, "categories": CATEGORIES,
                     "learned": all_learned_mappings()})


@app.route("/api/training/confirm", methods=["POST"])
def confirm():
    body = request.get_json(force=True)
    line = body["line"]
    device_id = body["device_id"]
    field = body["field"]
    value = body["value"]
    label = body["label"]

    if field != "ignore":
        confirm_mapping(line, field, value, label)
        device = DEVICES.get(device_id)
        if device:
            setattr(device.cdm, field, value)
            device.findings = evaluate(device.cdm, device.vendor)

    global PENDING
    PENDING = [p for p in PENDING if not (p["line"] == line and p["device_id"] == device_id)]
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
