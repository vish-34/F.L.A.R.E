"""
Audit logging for F.L.A.R.E Security Gateway.
Tracks all tool invocation attempts, user approvals/rejections, and execution outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
from pathlib import Path


@dataclass
class AuditRecord:
    timestamp: str
    tool_name: str
    tier: str
    params: Dict[str, Any]
    approved: bool
    status: str  # "EXECUTED", "REJECTED", "FAILED"
    reason: Optional[str] = None
    execution_time_ms: Optional[float] = None


class AuditLogger:
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file
        self.history: List[AuditRecord] = []

    def record(
        self,
        tool_name: str,
        tier: str,
        params: Dict[str, Any],
        approved: bool,
        status: str,
        reason: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
    ) -> AuditRecord:
        entry = AuditRecord(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tool_name=tool_name,
            tier=tier,
            params=params,
            approved=approved,
            status=status,
            reason=reason,
            execution_time_ms=execution_time_ms,
        )
        self.history.append(entry)

        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry.__dict__) + "\n")
            except Exception:
                pass

        return entry

    def get_recent(self, limit: int = 10) -> List[AuditRecord]:
        return self.history[-limit:]

    def clear(self):
        self.history.clear()
