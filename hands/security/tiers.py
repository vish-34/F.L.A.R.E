"""
Security Tiers Definition for F.L.A.R.E Hands.
Implements the 3-Tier Security Architecture specified in plan.md:
  🟢 SAFE: Auto-Execute (read-only, search, system telemetry)
  🟡 CONFIRM: Ask User First (launching apps, closing apps, editing files)
  🔴 STRICT: Explicit Danger Warning & Confirmation Required (killing processes, deleting files, shutdown)
"""

from enum import Enum


class SecurityTier(str, Enum):
    SAFE = "SAFE"        # 🟢 Tier 1: Auto-Execute
    CONFIRM = "CONFIRM"  # 🟡 Tier 2: Ask User First
    STRICT = "STRICT"    # 🔴 Tier 3: Strict Danger Confirmation


def get_tier_badge(tier: SecurityTier | str) -> str:
    """Return an emoji and text badge for the security tier."""
    t = SecurityTier(tier) if isinstance(tier, str) else tier
    if t == SecurityTier.SAFE:
        return "🟢 [SAFE]"
    elif t == SecurityTier.CONFIRM:
        return "🟡 [CONFIRM]"
    elif t == SecurityTier.STRICT:
        return "🔴 [STRICT]"
    return f"⚪ [{t.value}]"


def get_tier_description(tier: SecurityTier | str) -> str:
    """Return user-friendly policy explanation for a tier."""
    t = SecurityTier(tier) if isinstance(tier, str) else tier
    if t == SecurityTier.SAFE:
        return "Auto-executable read/search action. No system state modification."
    elif t == SecurityTier.CONFIRM:
        return "Modifies system state or user environment. Requires standard user authorization."
    elif t == SecurityTier.STRICT:
        return "Potentially disruptive or destructive action. Requires explicit danger confirmation."
    return "Unknown security tier policy."
