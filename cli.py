from __future__ import annotations

import json
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.main import build_result
from app.parsers.mcp_scan_input import normalize_mcp_scan
from app.report.pdf_generator import generate_pdf


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--domain", required=False)
@click.option("--autonomy", "autonomy_level", required=False)
@click.option("--oversight", "human_oversight", required=False, type=bool)
def scan(input_path: str, domain: str | None, autonomy_level: str | None, human_oversight: bool | None) -> None:
    payload = json.loads(Path(input_path).read_text())
    if domain:
        payload["domain"] = domain
    if autonomy_level:
        payload["autonomy_level"] = autonomy_level
    if human_oversight is not None:
        payload["human_oversight"] = human_oversight
    normalized = normalize_mcp_scan(payload)
    result = build_result(normalized)
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    scan_id = Path(input_path).stem
    env = Environment(loader=FileSystemLoader("app/report/templates"), autoescape=select_autoescape())
    dashboard_html = env.get_template("dashboard.html").render(scan_id=scan_id, days_until_enforcement=27, **result)
    dashboard_path = reports / f"{scan_id}-dashboard.html"
    pdf_path = reports / f"{scan_id}-report.pdf"
    dashboard_path.write_text(dashboard_html)
    generate_pdf(scan_id, result, pdf_path)
    click.echo(f"Tier: {result['tier']} | Score: {result['score']}/100 | Confidence: {result['confidence']:.0%}")
    click.echo(f"Dashboard: {dashboard_path}")
    click.echo(f"PDF: {pdf_path}")


if __name__ == "__main__":
    cli()
