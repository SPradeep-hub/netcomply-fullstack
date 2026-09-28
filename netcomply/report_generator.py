"""
report_generator.py
Builds the per-device compliance PDF using ReportLab, as named in the
problem statement's suggested workflow. Covers device ID, pass/fail findings
with severity, and remediation commands -- the four sections it requires.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from models import Device


def generate_pdf(device: Device, out_path: str):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=14)
    body = styles["BodyText"]
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, textColor=colors.grey)

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                             topMargin=18 * mm, bottomMargin=18 * mm)
    story = []

    story.append(Paragraph("NetComply — Network Security Compliance Report", title_style))
    story.append(Spacer(1, 10))

    # Device Identification
    story.append(Paragraph("Device Identification", h2))
    info_table = Table([
        ["Hostname", device.cdm.hostname],
        ["Vendor", device.vendor],
        ["OS", device.cdm.os],
        ["Serial Number", device.cdm.serial],
        ["Source File", device.filename],
        ["Compliance Score", f"{device.score}%"],
    ], colWidths=[110, 350])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)

    # Compliance Findings
    story.append(Paragraph("Compliance Findings", h2))
    sev_color = {"HIGH": colors.HexColor("#c0392b"),
                 "MEDIUM": colors.HexColor("#b7791f"),
                 "LOW": colors.HexColor("#2b6cb0")}
    rows = [["Rule", "Framework", "Severity", "Result"]]
    for f in device.findings:
        rows.append([f.title, f.framework, f.severity, "PASS" if f.passed else "FAIL"])
    ftable = Table(rows, colWidths=[240, 60, 60, 60])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2130")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, f in enumerate(device.findings, start=1):
        color = colors.HexColor("#1a7f4b") if f.passed else colors.HexColor("#c0392b")
        style.append(("TEXTCOLOR", (3, i), (3, i), color))
    ftable.setStyle(TableStyle(style))
    story.append(ftable)

    # Remediation Paths (failed rules only)
    failed = [f for f in device.findings if not f.passed]
    if failed:
        story.append(Paragraph("Remediation Paths", h2))
        for f in failed:
            story.append(Paragraph(f"<b>{f.title}</b> ({f.severity})", body))
            story.append(Paragraph(f"Why it matters: {f.why}", small))
            code = f.remediation.replace("\n", "<br/>")
            story.append(Paragraph(
                f'<font face="Courier" size="8" color="#0b3d91">{code}</font>', body))
            story.append(Spacer(1, 8))

    doc.build(story)
    return out_path
