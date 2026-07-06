from __future__ import annotations

from typing import Any


OBLIGATIONS = [
    "risk management system",
    "data governance docs",
    "technical documentation",
    "record-keeping/logging",
    "transparency to users",
    "human oversight mechanism",
    "accuracy/robustness testing",
    "conformity assessment",
]

TIER_REQUIREMENTS = {
    "unacceptable": OBLIGATIONS,
    "high-risk": OBLIGATIONS,
    "limited-risk": [
        "record-keeping/logging",
        "transparency to users",
        "technical documentation",
        "accuracy/robustness testing",
    ],
    "minimal-risk": ["record-keeping/logging", "technical documentation"],
}


def _evidence(scan: dict[str, Any], obligation: str) -> tuple[str, str]:
    docs = set(scan.get("documentation", []) or [])
    tests = set(scan.get("tests", []) or [])
    controls = set(scan.get("controls", []) or [])
    logging_present = bool(scan.get("logging_present", False))
    human_oversight = bool(scan.get("human_oversight", False))
    wildcard_scopes = scan.get("wildcard_scopes", []) or []
    credential_issues = scan.get("credential_scope_issues", []) or []

    if obligation == "risk management system":
        return ("met", "Risk register or risk management evidence found.") if "risk_register" in docs else ("gap", "No risk management system evidence was supplied.")
    if obligation == "data governance docs":
        return ("met", "Data governance documentation is present.") if "data_governance" in docs else ("gap", "No data governance documentation was detected.")
    if obligation == "technical documentation":
        return ("met", "Technical documentation is present.") if "technical_docs" in docs else ("partial", "Tool inventory exists, but formal technical documentation is incomplete.")
    if obligation == "record-keeping/logging":
        if logging_present and not wildcard_scopes:
            return "met", "Logging is enabled and no wildcard tool scopes were detected."
        if logging_present:
            return "partial", "Logging is enabled, but wildcard permissions reduce auditability."
        return "gap", "No reliable logging or record-keeping signal was found."
    if obligation == "transparency to users":
        return ("met", "User-facing AI disclosure is present.") if "user_disclosure" in controls else ("gap", "No transparency notice or AI disclosure control was supplied.")
    if obligation == "human oversight mechanism":
        return ("met", "Human oversight is enabled.") if human_oversight else ("gap", "No human oversight mechanism is configured.")
    if obligation == "accuracy/robustness testing":
        return ("met", "Robustness or red-team testing evidence is present.") if tests & {"robustness", "red_team"} else ("gap", "No accuracy, robustness, or red-team test evidence was supplied.")
    if obligation == "conformity assessment":
        if "conformity_assessment" in docs and not credential_issues:
            return "met", "Conformity assessment evidence is present and credential scope issues are absent."
        if "conformity_assessment" in docs:
            return "partial", "Conformity assessment exists, but credential scope issues remain unresolved."
        return "gap", "No conformity assessment evidence was supplied."
    return "gap", "No evidence mapped to this obligation."


def analyze_gaps(tier: str, scan: dict[str, Any]) -> list[dict[str, str]]:
    required = set(TIER_REQUIREMENTS.get(tier, OBLIGATIONS))
    results: list[dict[str, str]] = []
    for obligation in OBLIGATIONS:
        if obligation not in required:
            results.append(
                {
                    "obligation": obligation,
                    "status": "met",
                    "reason": f"Not mandatory for {tier}, tracked as good-practice evidence.",
                }
            )
            continue
        status, reason = _evidence(scan, obligation)
        results.append({"obligation": obligation, "status": status, "reason": reason})
    return results


def compliance_score(gaps: list[dict[str, str]]) -> int:
    weights = {"met": 1.0, "partial": 0.5, "gap": 0.0}
    if not gaps:
        return 0
    return round(sum(weights.get(item["status"], 0.0) for item in gaps) / len(gaps) * 100)
