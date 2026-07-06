from __future__ import annotations

from pathlib import Path
from textwrap import wrap
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape())


def render_report_html(scan_id: str, result: dict[str, Any]) -> str:
    template = env.get_template("report.html")
    return template.render(scan_id=scan_id, **result)


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _fallback_pdf(scan_id: str, result: dict[str, Any]) -> bytes:
    raw_lines = [
        "ComplianceGraph EU AI Act Compliance Assessment",
        f"Scan ID: {scan_id}",
        f"Tier: {result['tier'].upper()}",
        f"Score: {result['score']}/100",
        f"Confidence: {result['confidence']:.0%}",
        "Findings:",
    ]
    for finding in result["findings"][:14]:
        raw_lines.append(f"- {finding['obligation']}: {finding['status']} - {finding['reason']}")

    lines: list[str] = []
    for line in raw_lines:
        wrapped = wrap(line, width=72) or [""]
        lines.extend(wrapped)

    text_ops = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for line in lines[:48]:
        text_ops.append(f"({_escape_pdf_text(line)}) Tj")
        text_ops.append("T*")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(pdf)


def generate_pdf(scan_id: str, result: dict[str, Any], output_path: Path | None = None) -> bytes:
    html = render_report_html(scan_id, result)
    try:
        from weasyprint import HTML

        pdf = HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()
    except Exception:
        pdf = _fallback_pdf(scan_id, result)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf)
    return pdf
