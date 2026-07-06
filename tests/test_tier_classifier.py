import json
from pathlib import Path

from app.risk_engine.tier_classifier import classify_tier


FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text())


def test_high_risk_fixture_classifies_high_risk():
    assert classify_tier(load("high_risk_sample.json"))["tier"] == "high-risk"


def test_limited_risk_fixture_classifies_limited_risk():
    assert classify_tier(load("limited_risk_sample.json"))["tier"] == "limited-risk"


def test_minimal_risk_fixture_classifies_minimal_risk():
    assert classify_tier(load("minimal_risk_sample.json"))["tier"] == "minimal-risk"


def test_unacceptable_domain_wins():
    result = classify_tier({"domain": "social_scoring", "autonomy_level": "low"})
    assert result["tier"] == "unacceptable"
