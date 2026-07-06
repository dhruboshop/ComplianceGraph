from __future__ import annotations

import os
from typing import Any


def explain_gap(gap: dict[str, str], scan: dict[str, Any]) -> str:
    if not os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("COMPLIANCEGRAPH_DISABLE_LLM", "1") == "1":
        return f"{gap['reason']} Recommended next step: assign an owner, collect evidence, and retest this control before audit."
    return f"{gap['reason']} Recommended next step: document the control evidence and retest before audit."
