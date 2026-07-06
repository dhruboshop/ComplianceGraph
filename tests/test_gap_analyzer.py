import json
from pathlib import Path

from app.parsers.mcp_scan_input import normalize_mcp_scan
from app.risk_engine.gap_analyzer import analyze_gaps, compliance_score


FIXTURES = Path(__file__).parent / "fixtures"


def test_high_risk_gaps_include_human_oversight_gap():
    scan = normalize_mcp_scan(json.loads((FIXTURES / "high_risk_sample.json").read_text()))
    gaps = analyze_gaps("high-risk", scan)
    oversight = next(item for item in gaps if item["obligation"] == "human oversight mechanism")
    assert oversight["status"] == "gap"
    assert compliance_score(gaps) < 80


def test_minimal_risk_has_small_good_practice_surface():
    scan = normalize_mcp_scan(json.loads((FIXTURES / "minimal_risk_sample.json").read_text()))
    gaps = analyze_gaps("minimal-risk", scan)
    assert len(gaps) == 8
    assert next(item for item in gaps if item["obligation"] == "record-keeping/logging")["status"] == "met"
