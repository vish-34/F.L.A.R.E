"""
Unified Tool Registry for F.L.A.R.E Hands.
Manages tool definitions, security tier policies, JSON schemas for LLM tool calling,
and guarded execution.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from hands.browser_tools.media_player import MediaPlayer
from hands.browser_tools.web_navigator import WebNavigator
from hands.developer_tools.code_writer import CodeWriter
from hands.developer_tools.script_runner import ScriptRunner
from hands.file_tools.windows_search import WindowsSearch
from hands.security.security_guard import SecurityGuard
from hands.security.tiers import SecurityTier, get_tier_badge
from hands.system_control.app_manager import AppManager
from hands.system_control.audio_control import AudioControl
from hands.system_control.file_organizer import FileOrganizer
from hands.system_control.screen_tools import ScreenTools


@dataclass
class ToolDefinition:
    name: str
    description: str
    tier: SecurityTier
    parameters: Dict[str, Any]
    func: Callable[..., Any]


class ToolRegistry:
    """Registry that provides schema generation and secure guarded tool execution."""

    def __init__(self, security_guard: Optional[SecurityGuard] = None):
        self.guard = security_guard or SecurityGuard()
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(
        self,
        name: str,
        description: str,
        tier: SecurityTier,
        parameters: Dict[str, Any],
        func: Callable[..., Any],
    ):
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            tier=tier,
            parameters=parameters,
            func=func,
        )

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of tool descriptions with their assigned security tier."""
        return [
            {
                "name": t.name,
                "tier": t.tier.value,
                "badge": get_tier_badge(t.tier),
                "description": t.description,
            }
            for t in self.tools.values()
        ]

    def export_schemas(self) -> List[Dict[str, Any]]:
        """
        Export tools formatted for OpenAI / LiteLLM function calling:
        [
            {
                "type": "function",
                "function": {
                    "name": "...",
                    "description": "...",
                    "parameters": {...}
                }
            }
        ]
        """
        schemas = []
        for tool in self.tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": f"[{tool.tier.value}] {tool.description}",
                    "parameters": tool.parameters,
                },
            })
        return schemas

    def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool through the triple-tier Security Guard."""
        tool = self.tools.get(tool_name)
        if not tool:
            return {
                "success": False,
                "tool": tool_name,
                "tier": "UNKNOWN",
                "data": None,
                "error": f"Tool '{tool_name}' not found in registry.",
                "execution_time_ms": 0.0,
            }

        return self.guard.execute_guarded(
            tool_name=tool.name,
            tier=tool.tier,
            func=tool.func,
            params=kwargs,
            description=tool.description,
        )

    def _register_default_tools(self):
        """Register the built-in Phase 2 Windows operating tools."""

        # 1. Open Application (🟡 CONFIRM)
        self.register(
            name="open_app",
            description="Launch a desktop application, program executable, or Windows URI scheme.",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "app_identifier": {
                        "type": "string",
                        "description": "App alias (notepad, calc, chrome, code, spotify), executable name, or URI protocol.",
                    },
                    "arguments": {
                        "type": "string",
                        "description": "Optional command-line arguments to pass to the application.",
                    },
                },
                "required": ["app_identifier"],
            },
            func=AppManager.open_app,
        )

        # 2. List Running Applications (🟢 SAFE)
        self.register(
            name="list_running_apps",
            description="List active visible applications and their process IDs and window titles.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "include_background": {
                        "type": "boolean",
                        "description": "If true, also includes background services without GUI windows.",
                        "default": False,
                    }
                },
            },
            func=AppManager.list_running_apps,
        )

        # 3. Close Application (🟡 CONFIRM)
        self.register(
            name="close_app",
            description="Gracefully close an application window or process by name or PID.",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "app_identifier": {
                        "type": "string",
                        "description": "Process name (e.g. 'notepad', 'chrome.exe') or numeric process PID.",
                    }
                },
                "required": ["app_identifier"],
            },
            func=AppManager.close_app,
        )

        # 4. Force Kill Application (🔴 STRICT)
        self.register(
            name="force_kill_app",
            description="Forcefully terminate an application and all its child processes immediately. Use only when graceful close fails.",
            tier=SecurityTier.STRICT,
            parameters={
                "type": "object",
                "properties": {
                    "app_identifier": {
                        "type": "string",
                        "description": "Process name or numeric PID to forcefully kill.",
                    }
                },
                "required": ["app_identifier"],
            },
            func=AppManager.force_kill_app,
        )

        # 5. Search Files (🟢 SAFE)
        self.register(
            name="search_files",
            description="Search for files by keyword or glob pattern (*.py, *.pdf) across Windows directories.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Filename, keyword, or glob pattern to search for.",
                    },
                    "search_root": {
                        "type": "string",
                        "description": "Starting directory path. If omitted, searches user Desktop, Documents, Downloads.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return.",
                        "default": 25,
                    },
                    "extension": {
                        "type": "string",
                        "description": "Filter by file extension (e.g. 'py', 'pdf', 'docx').",
                    },
                },
                "required": ["query"],
            },
            func=WindowsSearch.search_files,
        )

        # 6. Find Installed Application (🟢 SAFE)
        self.register(
            name="find_installed_app",
            description="Find installed applications and shortcuts from the Windows Start Menu and PATH.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name or keyword of the application to search for.",
                    }
                },
                "required": ["app_name"],
            },
            func=WindowsSearch.find_installed_app,
        )

        # 7. Read File Preview (🟢 SAFE)
        self.register(
            name="read_file_preview",
            description="Safely read the first few lines of a text or code document.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file.",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Number of lines to preview (default: 50).",
                        "default": 50,
                    },
                },
                "required": ["file_path"],
            },
            func=WindowsSearch.read_file_preview,
        )

        # 8. Play Media (YouTube / Spotify) (🟡 CONFIRM)
        self.register(
            name="play_media",
            description="Play music, video, or podcast on YouTube or Spotify in a browser.",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Song name, artist, video title, or album.",
                    },
                    "platform": {
                        "type": "string",
                        "description": "Platform to play on ('youtube', 'spotify', 'soundcloud').",
                        "default": "youtube",
                    },
                    "browser": {
                        "type": "string",
                        "description": "Browser to use ('brave', 'chrome', 'edge', 'default').",
                        "default": "brave",
                    },
                },
                "required": ["query"],
            },
            func=MediaPlayer.play_media,
        )

        # 9. Hardware Media Key Controls (🟢 SAFE)
        self.register(
            name="media_control",
            description="Control media playback via hardware keys (play_pause, next, prev, stop, mute, vol_up, vol_down).",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'play_pause', 'next', 'prev', 'stop', 'mute', 'vol_up', 'vol_down'.",
                    }
                },
                "required": ["action"],
            },
            func=MediaPlayer.media_control,
        )

        # 10. Web Search and Open (🟡 CONFIRM)
        self.register(
            name="search_web_and_open",
            description="Search the web across Google, Brave, GitHub, Reddit, or YouTube and open in browser.",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query keywords.",
                    },
                    "engine": {
                        "type": "string",
                        "description": "Search engine ('google', 'brave', 'github', 'reddit', 'youtube').",
                        "default": "brave",
                    },
                    "browser": {
                        "type": "string",
                        "description": "Browser to use ('brave', 'chrome', 'edge', 'default').",
                        "default": "brave",
                    },
                },
                "required": ["query"],
            },
            func=WebNavigator.search_web_and_open,
        )

        # 11. Create Code Script (🟡 CONFIRM)
        self.register(
            name="create_script",
            description="Create a syntax-validated script file and optionally open it in an editor (code, notepad).",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Script file name (e.g. 'script.py', 'scraper.py').",
                    },
                    "code_content": {
                        "type": "string",
                        "description": "Full source code content of the script.",
                    },
                    "target_directory": {
                        "type": "string",
                        "description": "Destination directory: 'workspace', 'desktop', 'documents', or custom path.",
                        "default": "workspace",
                    },
                    "open_in_editor": {
                        "type": "string",
                        "description": "Editor to launch ('code' for VS Code, 'notepad', or null).",
                        "default": "code",
                    },
                },
                "required": ["filename", "code_content"],
            },
            func=CodeWriter.create_script,
        )

        # 12. Run Python Script (🟡 CONFIRM)
        self.register(
            name="run_python_script",
            description="Execute a Python script safely in subprocess, capturing output and diagnosing errors.",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "script_path": {
                        "type": "string",
                        "description": "Path to the Python script.",
                    },
                    "arguments": {
                        "type": "string",
                        "description": "Optional command-line arguments to pass.",
                    },
                    "timeout_sec": {
                        "type": "number",
                        "description": "Timeout in seconds (default: 30).",
                        "default": 30,
                    },
                },
                "required": ["script_path"],
            },
            func=ScriptRunner.run_python_script,
        )

        # 13. System Master Volume (🟢 SAFE)
        self.register(
            name="set_volume",
            description="Set master audio volume percentage (0 to 100).",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "level_percent": {
                        "type": "integer",
                        "description": "Target volume percentage from 0 to 100.",
                    }
                },
                "required": ["level_percent"],
            },
            func=AudioControl.set_volume,
        )

        # 14. Adjust Volume (🟢 SAFE)
        self.register(
            name="adjust_volume",
            description="Step master volume up or down.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "'up' or 'down'.",
                        "default": "up",
                    },
                    "steps": {
                        "type": "integer",
                        "description": "Number of adjustment steps (approx 2% per step).",
                        "default": 5,
                    },
                },
            },
            func=AudioControl.adjust_volume,
        )

        # 15. Toggle Mute (🟢 SAFE)
        self.register(
            name="toggle_mute",
            description="Toggle audio mute on or off.",
            tier=SecurityTier.SAFE,
            parameters={"type": "object", "properties": {}},
            func=AudioControl.toggle_mute,
        )

        # 16. Get System Vitals HUD (🟢 SAFE)
        self.register(
            name="get_system_vitals",
            description="Get real-time CPU, RAM, Disk, and Battery diagnostics.",
            tier=SecurityTier.SAFE,
            parameters={"type": "object", "properties": {}},
            func=AppManager.get_system_vitals,
        )

        # 17. Get/Set Clipboard (🟢 SAFE)
        self.register(
            name="get_clipboard",
            description="Read text from the Windows clipboard.",
            tier=SecurityTier.SAFE,
            parameters={"type": "object", "properties": {}},
            func=AppManager.get_clipboard,
        )
        self.register(
            name="set_clipboard",
            description="Copy text to the Windows clipboard.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy to clipboard."}
                },
                "required": ["text"],
            },
            func=AppManager.set_clipboard,
        )

        # 18. Minimize All Windows (Show Desktop) (🟢 SAFE)
        self.register(
            name="minimize_all_windows",
            description="Minimize all open windows and show the desktop.",
            tier=SecurityTier.SAFE,
            parameters={"type": "object", "properties": {}},
            func=AppManager.minimize_all_windows,
        )

        # 19. Send Hotkey (🟡 CONFIRM)
        self.register(
            name="send_hotkey",
            description="Trigger a keyboard hotkey (e.g. 'ctrl+s', 'alt+tab', 'win+d', 'ctrl+w').",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "hotkey": {
                        "type": "string",
                        "description": "Hotkey string (e.g. 'ctrl+s', 'alt+tab', 'win+d').",
                    }
                },
                "required": ["hotkey"],
            },
            func=AppManager.send_hotkey,
        )

        # 19b. Tab & Window Navigation (🟢 SAFE)
        self.register(
            name="switch_tab",
            description="Switch to next or previous tab in active or target browser.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "description": "'next' or 'prev'", "default": "next"},
                    "app_target": {"type": "string", "description": "Target browser (brave, chrome, edge)", "default": None},
                },
            },
            func=AppManager.switch_tab,
        )

        self.register(
            name="new_tab",
            description="Open a new tab (Ctrl+T) in the browser.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "app_target": {"type": "string", "description": "Target browser (brave, chrome, edge)", "default": None},
                },
            },
            func=AppManager.new_tab,
        )

        self.register(
            name="close_tab",
            description="Close the active tab (Ctrl+W) in the browser.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "app_target": {"type": "string", "description": "Target browser (brave, chrome, edge)", "default": None},
                },
            },
            func=AppManager.close_tab,
        )

        self.register(
            name="switch_window",
            description="Switch to the next application window (Alt+Tab).",
            tier=SecurityTier.SAFE,
            parameters={"type": "object", "properties": {}},
            func=AppManager.switch_window,
        )

        # 20. Take Screenshot (🟢 SAFE)
        self.register(
            name="take_screenshot",
            description="Capture a desktop screenshot and save to Pictures or Desktop.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional custom filename.",
                    },
                    "target_directory": {
                        "type": "string",
                        "description": "'pictures' or 'desktop'.",
                        "default": "pictures",
                    },
                },
            },
            func=ScreenTools.take_screenshot,
        )

        # 21. Organize Directory (🟡 CONFIRM)
        self.register(
            name="organize_directory",
            description="Organize loose files in Downloads or Desktop into categorized subfolders (Documents, Images, Videos, Installers, Archives).",
            tier=SecurityTier.CONFIRM,
            parameters={
                "type": "object",
                "properties": {
                    "target_directory": {
                        "type": "string",
                        "description": "'downloads' or 'desktop' or custom directory path.",
                        "default": "downloads",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulates changes without moving files.",
                        "default": False,
                    },
                },
            },
            func=FileOrganizer.organize_directory,
        )

        # 22. Task View (All apps in small windows) (🟢 SAFE)
        self.register(
            name="show_task_view",
            description="Open Windows Task View (Win + Tab) to tile all open windows like a 3-finger touchpad swipe.",
            tier=SecurityTier.SAFE,
            parameters={"type": "object", "properties": {}},
            func=AppManager.show_task_view,
        )

        # 23. List Open Apps Formatted (🟢 SAFE)
        self.register(
            name="format_running_apps",
            description="List all active open applications with process IDs and window titles in a clean list.",
            tier=SecurityTier.SAFE,
            parameters={"type": "object", "properties": {}},
            func=AppManager.format_running_apps,
        )

        # 24. Switch and Fullscreen App (🟢 SAFE)
        self.register(
            name="switch_and_fullscreen_app",
            description="Switch to an application, minimize other open windows, and maximize it to full screen.",
            tier=SecurityTier.SAFE,
            parameters={
                "type": "object",
                "properties": {
                    "app_identifier": {
                        "type": "string",
                        "description": "Name of the app (e.g. 'brave', 'code', 'notepad', 'chrome', 'spotify').",
                    },
                    "minimize_others": {
                        "type": "boolean",
                        "description": "Whether to minimize other open windows first.",
                        "default": True,
                    },
                },
                "required": ["app_identifier"],
            },
            func=AppManager.switch_and_fullscreen_app,
        )

