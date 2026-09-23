"""
F.L.A.R.E Hands Package.
Computer Operating Tools, Triple-Tier Security Gateway, and Action Orchestrator.
"""

import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from hands.browser_tools.media_player import MediaPlayer
from hands.browser_tools.web_navigator import WebNavigator
from hands.developer_tools.code_writer import CodeWriter
from hands.developer_tools.script_runner import ScriptRunner
from hands.file_tools.windows_search import WindowsSearch
from hands.orchestrator import HandsOrchestrator
from hands.registry import ToolRegistry
from hands.security.audit import AuditLogger, AuditRecord
from hands.security.security_guard import SecurityGuard
from hands.security.tiers import SecurityTier, get_tier_badge, get_tier_description
from hands.system_control.app_manager import AppManager
from hands.system_control.audio_control import AudioControl
from hands.system_control.file_organizer import FileOrganizer
from hands.system_control.screen_tools import ScreenTools

__all__ = [
    "SecurityTier",
    "get_tier_badge",
    "get_tier_description",
    "AuditLogger",
    "AuditRecord",
    "SecurityGuard",
    "AppManager",
    "WindowsSearch",
    "ToolRegistry",
    "MediaPlayer",
    "WebNavigator",
    "CodeWriter",
    "ScriptRunner",
    "AudioControl",
    "FileOrganizer",
    "ScreenTools",
    "HandsOrchestrator",
]
