import json
from pathlib import Path

from app.parsers.manual_input import normalize_manual_input
from app.parsers.mcp_scan_input import normalize_mcp_scan


FIXTURES = Path(__file__).parent / "fixtures"


def test_mcp_parser_extracts_security_shapes():
    scan = normalize_mcp_scan(json.loads((FIXTURES / "high_risk_sample.json").read_text()))
    assert scan["logging_present"] is True
    assert "crm_export" in scan["wildcard_scopes"]
    assert "crm_export" in scan["credential_scope_issues"]
    assert scan["tool_capabilities"][0]["name"] == "loan_decision_api"


def test_manual_parser_outputs_classifier_shape():
    scan = normalize_manual_input({"domain": "finance", "autonomy_level": "high", "oversight": False})
    assert {"domain", "autonomy_level", "human_oversight", "logging_present"} <= set(scan)
