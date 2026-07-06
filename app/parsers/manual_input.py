from __future__ import annotations

from typing import Any


def normalize_manual_input(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": payload.get("domain", "internal"),
        "autonomy_level": payload.get("autonomy_level", "low"),
        "human_oversight": bool(payload.get("human_oversight", False)),
        "decision_impacts_persons": bool(payload.get("decision_impacts_persons", False)),
        "logging_present": bool(payload.get("logging_present", False)),
        "customer_facing": bool(payload.get("customer_facing", False)),
        "generative_or_chat": bool(payload.get("generative_or_chat", False)),
        "external_impact": bool(payload.get("external_impact", False)),
        "tool_capabilities": payload.get("tool_capabilities", []),
        "wildcard_scopes": payload.get("wildcard_scopes", []),
        "credential_scope_issues": payload.get("credential_scope_issues", []),
        "documentation": payload.get("documentation", []),
        "controls": payload.get("controls", []),
        "tests": payload.get("tests", []),
    }
