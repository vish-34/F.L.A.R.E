"""System control, process management, audio, screen, and file organization for F.L.A.R.E Hands."""

from hands.system_control.app_manager import AppManager, KNOWN_APP_ALIASES
from hands.system_control.audio_control import AudioControl
from hands.system_control.file_organizer import FileOrganizer
from hands.system_control.screen_tools import ScreenTools

__all__ = [
    "AppManager",
    "KNOWN_APP_ALIASES",
    "AudioControl",
    "FileOrganizer",
    "ScreenTools",
]
