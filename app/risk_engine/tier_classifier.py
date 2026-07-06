from __future__ import annotations

from typing import Any


UNACCEPTABLE_DOMAINS = {"biometric_id", "social_scoring", "subliminal_manipulation"}
HIGH_RISK_DOMAINS = {
    "finance",
    "health",
    "employment",
    "law_enforcement",
    "critical_infrastructure",
    "education",
}
TIER_ORDER = ["minimal-risk", "limited-risk", "high-risk", "unacceptable"]


def _escalate(tier: str) -> str:
    index = min(TIER_ORDER.index(tier) + 1, TIER_ORDER.index("high-risk"))
    return TIER_ORDER[index]


def classify_tier(scan: dict[str, Any]) -> dict[str, Any]:
    domain = str(scan.get("domain", "internal")).lower()
    autonomy_level = str(scan.get("autonomy_level", "low")).lower()
    human_oversight = bool(scan.get("human_oversight", False))
    impacts_persons = bool(scan.get("decision_impacts_persons", False))
    customer_facing = bool(scan.get("customer_facing", False))
    generative = bool(scan.get("generative_or_chat", False))
    external_impact = bool(scan.get("external_impact", impacts_persons or customer_facing))

    factors: list[str] = []

    if domain in UNACCEPTABLE_DOMAINS:
        tier = "unacceptable"
        factors.append(f"Domain '{domain}' is prohibited or unacceptable under EU AI Act rules.")
    elif domain in HIGH_RISK_DOMAINS and impacts_persons:
        tier = "high-risk"
        factors.append(f"Domain '{domain}' affects persons and maps to high-risk use cases.")
    elif customer_facing and generative and not impacts_persons:
        tier = "limited-risk"
        factors.append("Customer-facing generative/chat system without persistent decision authority.")
    elif not external_impact and domain in {"internal", "sandbox", "sandboxed"}:
        tier = "minimal-risk"
        factors.append("Internal or sandboxed system with no external impact.")
    else:
        tier = "minimal-risk"
        factors.append("No high-risk domain, prohibited practice, or persistent external decision impact detected.")

    if autonomy_level == "high" and not human_oversight and tier != "unacceptable":
        old_tier = tier
        tier = _escalate(tier)
        factors.append(f"Escalated from {old_tier} because autonomy is high and human oversight is absent.")

    confidence = {
        "unacceptable": 0.96,
        "high-risk": 0.9,
        "limited-risk": 0.84,
        "minimal-risk": 0.82,
    }[tier]

    return {"tier": tier, "confidence": confidence, "triggering_factors": factors}
