from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.db.models import get_scan, init_db, save_scan
from app.parsers.mcp_scan_input import normalize_mcp_scan
from app.report.pdf_generator import generate_pdf
from app.risk_engine.gap_analyzer import analyze_gaps, compliance_score
from app.risk_engine.llm_explainer import explain_gap
from app.risk_engine.tier_classifier import classify_tier


app = FastAPI(title="ComplianceGraph")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Environment(loader=FileSystemLoader("app/report/templates"), autoescape=select_autoescape())


@app.on_event("startup")
def startup() -> None:
    init_db()


def build_result(normalized: dict[str, Any]) -> dict[str, Any]:
    tier_result = classify_tier(normalized)
    gaps = analyze_gaps(tier_result["tier"], normalized)
    severity_rank = {"gap": 3, "partial": 2, "met": 1}
    severity = {"gap": "High", "partial": "Medium", "met": "Low"}
    findings = [
        {
            **gap,
            "severity": severity[gap["status"]],
            "severity_rank": severity_rank[gap["status"]],
            "explanation": explain_gap(gap, normalized),
        }
        for gap in gaps
    ]
    score = compliance_score(gaps)
    chart = {
        "labels": [item["obligation"] for item in findings],
        "met": [100 if item["status"] == "met" else 50 if item["status"] == "partial" else 0 for item in findings],
        "gaps": [0 if item["status"] == "met" else 50 if item["status"] == "partial" else 100 for item in findings],
    }
    return {**tier_result, "findings": findings, "score": score, "chart": chart}


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ComplianceGraph"}


@app.post("/scan")
def scan(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_mcp_scan(payload)
    result = build_result(normalized)
    scan_id = uuid.uuid4().hex[:12]
    save_scan(scan_id, payload, normalized, result)
    return {"scan_id": scan_id, "tier": result["tier"], "confidence": result["confidence"], "score": result["score"]}


def _demo_scan(scan_id: str) -> dict[str, Any]:
    sample = {
        "domain": "finance",
        "autonomy_level": "high",
        "human_oversight": False,
        "decision_impacts_persons": True,
        "logging_present": True,
        "documentation": ["technical_docs", "risk_register"],
        "tests": ["red_team"],
        "tools": [{"name": "crm_export", "permissions": ["customer:*", "read:secret_tokens"]}],
    }
    normalized = normalize_mcp_scan(sample)
    return {"id": scan_id, "normalized": normalized, "result": build_result(normalized)}


@app.get("/dashboard/{scan_id}", response_class=HTMLResponse)
def dashboard(scan_id: str) -> HTMLResponse:
    record = get_scan(scan_id) or (_demo_scan(scan_id) if scan_id == "test" else None)
    if record is None:
        raise HTTPException(status_code=404, detail="scan not found")
    template = templates.get_template("dashboard.html")
    days = (date(2026, 8, 2) - date.today()).days
    return HTMLResponse(template.render(scan_id=scan_id, days_until_enforcement=max(days, 0), **record["result"]))


@app.get("/report/{scan_id}/pdf")
def report_pdf(scan_id: str) -> Response:
    record = get_scan(scan_id) or (_demo_scan(scan_id) if scan_id == "test" else None)
    if record is None:
        raise HTTPException(status_code=404, detail="scan not found")
    pdf = generate_pdf(scan_id, record["result"])
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="compliancegraph-{scan_id}.pdf"'},
    )
