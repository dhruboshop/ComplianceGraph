from __future__ import annotations

from typing import Any

from app.parsers.manual_input import normalize_manual_input


def _extract_tools(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_tools = payload.get("tools") or payload.get("mcp_tools") or payload.get("capabilities") or []
    tools: list[dict[str, Any]] = []
    for item in raw_tools:
        if isinstance(item, str):
            tools.append({"name": item, "permissions": []})
        elif isinstance(item, dict):
            tools.append(
                {
                    "name": item.get("name") or item.get("tool") or "unnamed",
                    "permissions": item.get("permissions") or item.get("scopes") or [],
                }
            )
    return tools


def normalize_mcp_scan(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_manual_input(payload)
    tools = _extract_tools(payload)
    wildcard_scopes: list[str] = []
    credential_scope_issues: list[str] = []

    for tool in tools:
        permissions = [str(scope) for scope in tool.get("permissions", [])]
        if "*" in permissions or "admin:*" in permissions or any(scope.endswith(":*") for scope in permissions):
            wildcard_scopes.append(tool["name"])
        if any("credential" in scope or "secret" in scope or "token" in scope for scope in permissions):
            credential_scope_issues.append(tool["name"])

    findings = payload.get("findings", []) or payload.get("issues", []) or []
    for finding in findings:
        text = str(finding).lower()
        if "wildcard" in text:
            wildcard_scopes.append("scanner finding")
        if "credential" in text or "secret" in text or "token" in text:
            credential_scope_issues.append("scanner finding")

    normalized.update(
        {
            "tool_capabilities": tools,
            "wildcard_scopes": sorted(set(normalized.get("wildcard_scopes", []) + wildcard_scopes)),
            "credential_scope_issues": sorted(set(normalized.get("credential_scope_issues", []) + credential_scope_issues)),
            "logging_present": bool(payload.get("logging_present") or payload.get("logging", {}).get("enabled")),
        }
    )
    return normalized
