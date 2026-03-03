"""Execution policy gate for Tool Broker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable


@dataclass
class PolicyDecision:
    allowed: bool
    status_code: int = 200
    reason: str = "allowed"


class PolicyGate:
    """Narrow execution policy gate for allowlist and risk controls."""

    def __init__(
        self,
        allowed_tools: Iterable[str],
        high_risk_start_hour: int = 0,
        high_risk_end_hour: int = 23,
    ):
        self.allowed_tools = set(allowed_tools)
        self.high_risk_start_hour = high_risk_start_hour
        self.high_risk_end_hour = high_risk_end_hour

    def _is_high_risk(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        if tool_name != "ha_service_call":
            return False
        domain = str(arguments.get("domain", "")).lower()
        service = str(arguments.get("service", "")).lower()
        if domain in {"lock", "alarm_control_panel", "cover"}:
            return True
        if service in {"unlock", "open_cover", "disarm"}:
            return True
        return False

    def evaluate_execute(self, tool_name: str, arguments: Dict[str, Any]) -> PolicyDecision:
        if tool_name not in self.allowed_tools:
            return PolicyDecision(False, 403, f"Tool not allowed by policy: {tool_name}")

        if self._is_high_risk(tool_name, arguments):
            confirmed = bool(arguments.get("confirmed", False))
            if not confirmed:
                return PolicyDecision(
                    False,
                    403,
                    "Confirmation required for high-risk action. Set arguments.confirmed=true after user approval.",
                )

            hour = datetime.now().hour
            if not (self.high_risk_start_hour <= hour <= self.high_risk_end_hour):
                return PolicyDecision(
                    False,
                    403,
                    f"High-risk actions are blocked outside allowed hours ({self.high_risk_start_hour:02d}:00-{self.high_risk_end_hour:02d}:59).",
                )

        return PolicyDecision(True)
