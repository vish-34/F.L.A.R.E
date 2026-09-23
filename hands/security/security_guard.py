"""
Security Gateway & Permission Guard.
Enforces the 3-tier permission model before allowing any tool invocation.
"""

import sys
import time
from typing import Any, Callable, Dict, Optional, Tuple

from hands.security.audit import AuditLogger, AuditRecord
from hands.security.tiers import SecurityTier, get_tier_badge, get_tier_description


class SecurityGuard:
    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        confirm_callback: Optional[Callable[[str, SecurityTier, Dict[str, Any], str], bool]] = None,
        allow_all_for_testing: bool = False,
    ):
        self.audit = audit_logger or AuditLogger()
        self.confirm_callback = confirm_callback or self._default_cli_confirm
        self.allow_all_for_testing = allow_all_for_testing

    def _default_cli_confirm(
        self, tool_name: str, tier: SecurityTier, params: Dict[str, Any], description: str
    ) -> bool:
        """Default interactive CLI confirmation prompt."""
        badge = get_tier_badge(tier)

        if tier == SecurityTier.STRICT:
            print("\n" + "!" * 65)
            print(f"⚠️  SECURITY ALERT: {badge} ACTION REQUESTED")
            print(f"Tool        : {tool_name}")
            print(f"Parameters  : {params}")
            print(f"Description : {description}")
            print("WARNING: This action may cause process termination or file changes.")
            print("!" * 65)
            try:
                response = input("Type 'YES' to authorize this strict action: ").strip()
                return response == "YES"
            except (EOFError, KeyboardInterrupt):
                return False

        elif tier == SecurityTier.CONFIRM:
            print("\n" + "-" * 55)
            print(f"🛡️  PERMISSION REQUEST: {badge}")
            print(f"Tool       : {tool_name}")
            print(f"Parameters : {params}")
            print(f"Description: {description}")
            print("-" * 55)
            try:
                response = input("Authorize this action? [Y/n]: ").strip().lower()
                return response in ["y", "yes", ""]
            except (EOFError, KeyboardInterrupt):
                return False

        return True

    def check_permission(
        self,
        tool_name: str,
        tier: SecurityTier,
        params: Dict[str, Any],
        description: str = "",
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate permission for a tool invocation.
        Returns: (is_approved, reason)
        """
        if self.allow_all_for_testing:
            return True, "Authorized by test override mode."

        if tier == SecurityTier.SAFE:
            return True, "Safe action - auto-approved."

        # Tier is CONFIRM or STRICT: invoke confirmation handler
        is_approved = self.confirm_callback(tool_name, tier, params, description)
        if is_approved:
            return True, f"Authorized by user for {tier.value} tier."
        else:
            return False, f"Denied by user authorization prompt for {tier.value} tier."

    def execute_guarded(
        self,
        tool_name: str,
        tier: SecurityTier,
        func: Callable[..., Any],
        params: Dict[str, Any],
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Guard tool execution with security authorization and full audit logging.
        Returns standard result dict:
        {
            "success": bool,
            "tool": str,
            "tier": str,
            "data": Any,
            "error": Optional[str],
            "execution_time_ms": float
        }
        """
        start_time = time.perf_counter()
        approved, reason = self.check_permission(tool_name, tier, params, description)

        if not approved:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.audit.record(
                tool_name=tool_name,
                tier=tier.value,
                params=params,
                approved=False,
                status="REJECTED",
                reason=reason,
                execution_time_ms=elapsed_ms,
            )
            return {
                "success": False,
                "tool": tool_name,
                "tier": tier.value,
                "data": None,
                "error": f"Security Guard Blocked Action: {reason}",
                "execution_time_ms": round(elapsed_ms, 2),
            }

        # User approved (or SAFE tier) - proceed to execution
        try:
            result = func(**params)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.audit.record(
                tool_name=tool_name,
                tier=tier.value,
                params=params,
                approved=True,
                status="EXECUTED",
                reason="Successfully completed",
                execution_time_ms=elapsed_ms,
            )
            return {
                "success": True,
                "tool": tool_name,
                "tier": tier.value,
                "data": result,
                "error": None,
                "execution_time_ms": round(elapsed_ms, 2),
            }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.audit.record(
                tool_name=tool_name,
                tier=tier.value,
                params=params,
                approved=True,
                status="FAILED",
                reason=str(e),
                execution_time_ms=elapsed_ms,
            )
            return {
                "success": False,
                "tool": tool_name,
                "tier": tier.value,
                "data": None,
                "error": f"Tool execution failed: {str(e)}",
                "execution_time_ms": round(elapsed_ms, 2),
            }
