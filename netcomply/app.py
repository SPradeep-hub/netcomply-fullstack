"""
app.py
Flask front end for NetComply. Routes:
  /                 dashboard (aggregate stats across scanned devices)
  /upload           ingestion screen (upload/paste config)
  /analyze  (POST)  runs parse -> rule engine, redirects to dashboard
  /training         Interactive Training Interface for unrecognized lines
  /confirm  (POST)  admin confirms a category -> saved via nlp_classifier
  /report/<id>      findings + remediation for one device
  /report/<id>/pdf  downloads the ReportLab PDF

In-memory store for demo purposes; swap DEVICES/PENDING for a real DB in production.
"""
import os
import uuid
from flask import Flask, request, redirect, url_for, render_template_string, send_file

from models import CDM, Device
from parsers.detect import detect_and_parse
from rule_engine import evaluate
from nlp_classifier import classify_line, confirm_mapping, all_learned_mappings
from report_generator import generate_pdf

app = Flask(__name__)

DEVICES: dict[str, Device] = {}
PENDING: list[dict] = []   # {"device_id":.., "line":.., "suggestion": {...} | None}

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_configs")


# ---------- shared layout ----------
LAYOUT = """
<!doctype html><html><head><title>NetComply</title>
<style>
body{font-family:Segoe UI,sans-serif;background:#0b0e14;color:#e6ebf5;margin:0}
header{background:#131824;padding:14px 24px;border-bottom:1px solid #232c40;display:flex;gap:18px;align-items:center}
header b{color:#5eead4}
nav a{color:#8b96ac;text-decoration:none;margin-right:14px;font-size:.9rem}
nav a:hover{color:#fff}
main{max-width:960px;margin:24px auto;padding:0 20px}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th,td{padding:8px;border-bottom:1px solid #232c40;text-align:left}
.badge{padding:2px 9px;border-radius:20px;font-size:.75rem;font-weight:700}
.pass{background:#0f2e22;color:#34d399}.fail{background:#3a1414;color:#f87171}
.card{background:#131824;border:1px solid #232c40;border-radius:10px;padding:16px;display:inline-block;min-width:140px;margin:0 10px 10px 0}
.card .n{font-size:1.6rem;font-weight:700}
textarea{width:100%;min-height:180px;background:#131824;color:#e6ebf5;border:1px solid #232c40;border-radius:8px;font-family:Consolas,monospace;padding:10px}
select,button,input{font-family:inherit;background:#1a2130;color:#e6ebf5;border:1px solid #232c40;border-radius:6px;padding:7px 10px}
button{cursor:pointer}
.remed{background:#0d1420;border:1px solid #232c40;border-radius:6px;padding:8px;font-family:Consolas,monospace;font-size:.8rem;color:#5eead4}
</style></head>
<body>
<header><b>NetComply</b>
<nav><a href="/">Dashboard</a><a href="/upload">Upload &amp; Scan</a><a href="/training">AI Training ({{ pending_count }})</a></nav>
</header>
<main>{{ content|safe }}</main>
</body></html>
"""


def render(content_html, **ctx):
    return render_template_string(LAYOUT, content=render_template_string(content_html, **ctx),
                                   pending_count=len(PENDING))


# ---------- dashboard ----------
@app.route("/")
def dashboard():
    total = len(DEVICES)
    compliant = sum(1 for d in DEVICES.values() if d.score == 100)
    sev = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for d in DEVICES.values():
        for f in d.findings:
            if not f.passed:
                sev[f.severity] += 1

    tmpl = """
    <h1>Compliance Dashboard</h1>
    <div>
      <div class="card"><div class="n">{{ total }}</div>Devices Scanned</div>
      <div class="card"><div class="n" style="color:#34d399">{{ compliant }}</div>Compliant</div>
      <div class="card"><div class="n" style="color:#f87171">{{ total - compliant }}</div>Non-Compliant</div>
      <div class="card"><div class="n" style="color:#f87171">{{ sev.HIGH }}</div>High Findings</div>
      <div class="card"><div class="n" style="color:#fbbf24">{{ sev.MEDIUM }}</div>Medium Findings</div>
      <div class="card"><div class="n" style="color:#60a5fa">{{ sev.LOW }}</div>Low Findings</div>
    </div>
    <h2>Scanned Devices</h2>
    {% if devices %}
    <table><tr><th>Hostname</th><th>Vendor</th><th>OS</th><th>Score</th><th>Status</th><th></th></tr>
    {% for d in devices %}
    <tr><td>{{ d.cdm.hostname }}</td><td>{{ d.vendor }}</td><td>{{ d.cdm.os }}</td>
    <td>{{ d.score }}%</td>
    <td><span class="badge {{ 'pass' if d.score==100 else 'fail' }}">{{ 'COMPLIANT' if d.score==100 else 'NON-COMPLIANT' }}</span></td>
    <td><a href="/report/{{ d.id }}" style="color:#38bdf8">View Report</a></td></tr>
    {% endfor %}</table>
    {% else %}<p style="color:#8b96ac">No devices scanned yet. Go to Upload &amp; Scan.</p>{% endif %}
    """
    return render(tmpl, total=total, compliant=compliant, sev=sev, devices=list(DEVICES.values()))


# ---------- upload / ingestion ----------
@app.route("/upload")
def upload_page():
    samples = [f for f in os.listdir(SAMPLE_DIR)] if os.path.exists(SAMPLE_DIR) else []
    tmpl = """
    <h1>Upload Configuration</h1>
    <p style="color:#8b96ac">Paste a config, or load a sample vendor file.</p>
    <form method="post" action="/analyze">
    <select name="sample" onchange="this.form.submit()">
      <option value="">-- load sample --</option>
      {% for s in samples %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
    </select>
    <br><br>
    <textarea name="config_text" placeholder="Paste raw device configuration here"></textarea>
    <input type="hidden" name="filename" value="pasted-config.txt">
    <br><br><button type="submit">Analyze Configuration</button>
    </form>
    """
    return render(tmpl, samples=samples)


@app.route("/analyze", methods=["POST"])
def analyze():
    sample = request.form.get("sample")
    if sample:
        with open(os.path.join(SAMPLE_DIR, sample)) as f:
            text = f.read()
        filename = sample
    else:
        text = request.form.get("config_text", "")
        filename = request.form.get("filename", "config.txt")

    if not text.strip():
        return redirect(url_for("upload_page"))

    vendor, cdm, unrecognized = detect_and_parse(text)
    device_id = str(uuid.uuid4())[:8]
    findings = evaluate(cdm, vendor)
    device = Device(id=device_id, filename=filename, vendor=vendor, cdm=cdm,
                     findings=findings, raw_config=text)
    DEVICES[device_id] = device

    for line in unrecognized:
        suggestion = classify_line(line)
        auto = suggestion and suggestion.get("auto")
        if auto:
            setattr(cdm, suggestion["field"], suggestion["value"])
            device.findings = evaluate(cdm, vendor)
        else:
            PENDING.append({"device_id": device_id, "line": line, "suggestion": suggestion})

    return redirect(url_for("report", device_id=device_id))


# ---------- AI training loop ----------
@app.route("/training")
def training():
    tmpl = """
    <h1>AI Training Interface</h1>
    <p style="color:#8b96ac">Lines NetComply could not classify against known vendor syntax. Confirm the category so it is learned for next time.</p>
    {% if not pending %}<p style="color:#8b96ac">Nothing pending. Learned mappings so far: {{ learned|length }}</p>{% endif %}
    {% for item in pending %}
    <div style="background:#1a2130;border:1px solid #232c40;border-radius:8px;padding:12px;margin-bottom:10px">
      <code style="display:block;margin-bottom:8px;word-break:break-all">{{ item.line }}</code>
      {% if item.suggestion %}<p style="color:#5eead4;font-size:.85rem">AI suggests: {{ item.suggestion.category }}</p>{% endif %}
      <form method="post" action="/confirm">
        <input type="hidden" name="idx" value="{{ loop.index0 }}">
        <input type="hidden" name="line" value="{{ item.line }}">
        <input type="hidden" name="device_id" value="{{ item.device_id }}">
        <select name="category">
          <option value="">-- choose category --</option>
          {% for cat in categories %}
          <option value="{{ cat.field }}|{{ cat.value }}|{{ cat.label }}"
            {{ 'selected' if item.suggestion and item.suggestion.category==cat.label else '' }}>{{ cat.label }}</option>
          {% endfor %}
          <option value="ignore|_|ignore">Not security-relevant / ignore</option>
        </select>
        <button type="submit">Confirm &amp; Learn</button>
      </form>
    </div>
    {% endfor %}
    <h2>Learned Mappings</h2>
    <table><tr><th>Keyword</th><th>Category</th></tr>
    {% for k,v in learned.items() %}<tr><td>{{ k }}</td><td>{{ v.category }}</td></tr>{% endfor %}
    </table>
    """
    categories = [
        {"field": "session_timeout_set", "value": True, "label": "Session Timeout (Authentication / Session Security)"},
        {"field": "ssh_version", "value": 2, "label": "SSH Configuration"},
        {"field": "http_enabled", "value": True, "label": "HTTP Management Interface"},
        {"field": "logging_enabled", "value": True, "label": "Logging / Audit"},
        {"field": "telnet_enabled", "value": True, "label": "Telnet Access"},
        {"field": "ntp_configured", "value": True, "label": "Time Synchronization (NTP)"},
        {"field": "aaa_configured", "value": True, "label": "AAA / Centralized Authentication"},
        {"field": "snmp_detected", "value": True, "label": "SNMP"},
    ]
    return render(tmpl, pending=PENDING, categories=categories, learned=all_learned_mappings())


@app.route("/confirm", methods=["POST"])
def confirm():
    line = request.form["line"]
    device_id = request.form["device_id"]
    choice = request.form["category"]
    field, value, label = choice.split("|")

    if field != "ignore":
        value = True if value == "True" else (int(value) if value.isdigit() else value)
        confirm_mapping(line, field, value, label)
        device = DEVICES.get(device_id)
        if device:
            setattr(device.cdm, field, value)
            device.findings = evaluate(device.cdm, device.vendor)

    global PENDING
    PENDING = [p for p in PENDING if not (p["line"] == line and p["device_id"] == device_id)]
    return redirect(url_for("training"))


# ---------- reports ----------
@app.route("/report/<device_id>")
def report(device_id):
    device = DEVICES.get(device_id)
    if not device:
        return redirect(url_for("dashboard"))
    tmpl = """
    <h1>{{ d.cdm.hostname }}</h1>
    <p style="color:#8b96ac">Vendor: {{ d.vendor }} · OS: {{ d.cdm.os }} · Serial: {{ d.cdm.serial }} · Score: {{ d.score }}%</p>
    <a href="/report/{{ d.id }}/pdf" style="color:#38bdf8">⬇ Download PDF Report</a>
    <table style="margin-top:14px">
    <tr><th>Rule</th><th>Framework</th><th>Severity</th><th>Result</th></tr>
    {% for f in d.findings %}
    <tr><td>{{ f.title }}</td><td>{{ f.framework }}</td><td>{{ f.severity }}</td>
    <td><span class="badge {{ 'pass' if f.passed else 'fail' }}">{{ 'PASS' if f.passed else 'FAIL' }}</span></td></tr>
    {% if not f.passed %}
    <tr><td colspan="4"><div class="remed">{{ f.why }}<br>{{ f.remediation.replace('\\n','<br>')|safe }}</div></td></tr>
    {% endif %}
    {% endfor %}
    </table>
    """
    return render(tmpl, d=device)


@app.route("/report/<device_id>/pdf")
def report_pdf(device_id):
    device = DEVICES.get(device_id)
    if not device:
        return redirect(url_for("dashboard"))
    out_path = f"/tmp/{device.cdm.hostname}-report.pdf"
    generate_pdf(device, out_path)
    return send_file(out_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
