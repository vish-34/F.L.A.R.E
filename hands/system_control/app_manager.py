"""
Windows Application & Window Manager.
Provides capabilities to:
- Open applications by alias, executable name, URI, or path
- List running interactive applications with window titles
- Gracefully close applications
- Force terminate stubborn applications (Strict tier)
"""

import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional
import psutil

# Common Windows application shortcuts and aliases
KNOWN_APP_ALIASES: Dict[str, str] = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "chrome": "chrome.exe",
    "brave": "brave.exe",
    "edge": "msedge.exe",
    "msedge": "msedge.exe",
    "code": "code",
    "vscode": "code",
    "spotify": "spotify.exe",
    "paint": "mspaint.exe",
    "taskmgr": "taskmgr.exe",
}

# Windows URI Protocols
KNOWN_URI_SCHEMES = [
    "calculator:",
    "spotify:",
    "ms-settings:",
    "bingmaps:",
    "ms-clock:",
]


class AppManager:
    """Manages Windows applications, processes, and windows."""

    @staticmethod
    def find_app_executable(app_name: str) -> Optional[str]:
        """Locate real executable path on Windows for browsers, editors, and tools."""
        b = app_name.lower().strip()
        home = Path.home()
        if b == "brave":
            candidates = [
                home / "AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe",
                Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"),
                Path("C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"),
            ]
            for c in candidates:
                if c.exists():
                    return str(c)
        elif b in ["chrome", "google-chrome"]:
            candidates = [
                Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
                Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
                home / "AppData/Local/Google/Chrome/Application/chrome.exe",
            ]
            for c in candidates:
                if c.exists():
                    return str(c)
        elif b in ["edge", "msedge"]:
            candidates = [
                Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
                Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
            ]
            for c in candidates:
                if c.exists():
                    return str(c)
        elif b in ["code", "vscode"]:
            candidates = [
                home / "AppData/Local/Programs/Microsoft VS Code/Code.exe",
                Path("C:/Program Files/Microsoft VS Code/Code.exe"),
                Path("C:/Program Files (x86)/Microsoft VS Code/Code.exe"),
            ]
            for c in candidates:
                if c.exists():
                    return str(c)
        return None

    @staticmethod
    def open_app(app_identifier: str, arguments: Optional[str] = None) -> Dict[str, Any]:
        """
        Launch an application on Windows.
        Accepts alias (e.g. 'notepad', 'chrome', 'brave'), executable name, full path, or URI.
        """
        app_clean = app_identifier.strip()
        lower_name = app_clean.lower()

        # Check if it's a known URI scheme
        if any(lower_name.startswith(uri) for uri in KNOWN_URI_SCHEMES) or "://" in lower_name:
            try:
                os.startfile(app_clean)
                return {
                    "launched": True,
                    "target": app_clean,
                    "method": "windows_uri_protocol",
                    "status": "Application launched successfully via Windows URI protocol.",
                }
            except Exception as e:
                return {
                    "launched": False,
                    "target": app_clean,
                    "error": f"Failed to start URI: {str(e)}",
                }

        # Check for browser or tool executable resolution (Brave, Chrome, VS Code, etc.)
        resolved_exe = AppManager.find_app_executable(lower_name)
        target_executable = resolved_exe or KNOWN_APP_ALIASES.get(lower_name, app_clean)

        # Launch using detached subprocess so FLARE is never blocked
        try:
            cmd = [target_executable]
            if arguments:
                clean_arg = str(arguments).strip()
                # Strip wrapping quotes if caller passed them
                if (clean_arg.startswith('"') and clean_arg.endswith('"')) or (clean_arg.startswith("'") and clean_arg.endswith("'")):
                    unquoted = clean_arg[1:-1].strip()
                else:
                    unquoted = clean_arg

                if unquoted.startswith(("http://", "https://")):
                    cmd.append(unquoted)
                elif Path(unquoted).exists() or "\\" in unquoted or "/" in unquoted:
                    # Target is a file or folder path; keep as single argument without splitting spaces
                    cmd.append(unquoted)
                else:
                    try:
                        import shlex
                        cmd.extend(shlex.split(clean_arg, posix=False))
                    except Exception:
                        cmd.extend(clean_arg.split())

            # DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP flag for Windows
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            process = subprocess.Popen(
                cmd,
                creationflags=flags,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return {
                "launched": True,
                "target": target_executable,
                "pid": process.pid,
                "status": f"Application '{target_executable}' launched with PID {process.pid}.",
            }
        except FileNotFoundError:
            # If arguments is a URL, fallback to os.startfile(url)
            if arguments and arguments.startswith(("http://", "https://")):
                try:
                    os.startfile(arguments)
                    return {
                        "launched": True,
                        "target": arguments,
                        "method": "os_startfile_url",
                        "status": f"Opened '{arguments}' in default browser.",
                    }
                except Exception:
                    pass

            # Fallback 1: check Start Menu / Program shortcuts
            try:
                from hands.file_tools.windows_search import WindowsSearch
                shortcuts = [
                    s for s in WindowsSearch.find_installed_app(lower_name)
                    if s["path"].lower().endswith((".lnk", ".exe"))
                ]
                if shortcuts:
                    chosen = shortcuts[0]["path"]
                    os.startfile(chosen)
                    return {
                        "launched": True,
                        "target": chosen,
                        "method": "start_menu_shortcut",
                        "status": f"Application '{app_clean}' launched via shortcut '{shortcuts[0]['name']}'.",
                    }
            except Exception:
                pass

            # Fallback 2: attempt os.startfile in case it's in App Paths registry
            try:
                os.startfile(target_executable)
                return {
                    "launched": True,
                    "target": target_executable,
                    "method": "os_startfile",
                    "status": f"Application '{target_executable}' launched via Windows shell.",
                }
            except Exception as ex:
                return {
                    "launched": False,
                    "target": target_executable,
                    "error": f"Executable not found in PATH or standard locations: {str(ex)}",
                }
        except Exception as e:
            return {
                "launched": False,
                "target": target_executable,
                "error": f"Failed to launch: {str(e)}",
            }

    @staticmethod
    def list_running_apps(include_background: bool = False) -> List[Dict[str, Any]]:
        """
        List currently running Windows applications.
        By default, filters for interactive user applications and excludes Windows system daemons.
        """
        SYSTEM_HELPERS = {
            "svchost.exe", "runtimebroker.exe", "conhost.exe", "sihost.exe",
            "searchhost.exe", "taskhostw.exe", "backgroundtaskhost.exe", "ctfmon.exe",
            "textinputhost.exe", "shellexperiencehost.exe", "smartscreen.exe",
            "startmenuexperiencehost.exe", "applicationframehost.exe", "wmiprvse.exe",
            "mousocoreworker.exe", "securityhealthsystray.exe", "userctxservice.exe",
            "gameinputsvc.exe", "spoolsv.exe",
        }

        # Attempt to grab window titles via quick PowerShell query if possible (with 2s timeout)
        window_titles: Dict[int, str] = {}
        try:
            ps_cmd = [
                "powershell", "-NoProfile", "-Command",
                "Get-Process | Where-Object MainWindowTitle | Select-Object -Property Id, MainWindowTitle | ConvertTo-Csv -NoTypeInformation"
            ]
            raw = subprocess.check_output(ps_cmd, text=True, timeout=2.5, stderr=subprocess.DEVNULL)
            import csv, io
            reader = csv.DictReader(io.StringIO(raw.strip()))
            for row in reader:
                pid_val = row.get("Id")
                title_val = row.get("MainWindowTitle")
                if pid_val and title_val:
                    window_titles[int(pid_val)] = title_val
        except Exception:
            pass

        apps_by_name: Dict[str, Dict[str, Any]] = {}

        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'memory_info']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                if not name:
                    continue

                username = proc.info.get('username') or ""
                # Skip system/service processes if background is not requested
                if not include_background:
                    u_lower = username.lower()
                    if "system" in u_lower or "service" in u_lower:
                        continue
                    if name.lower() in SYSTEM_HELPERS:
                        continue

                mem_mb = round(proc.info['memory_info'].rss / (1024 * 1024), 1) if proc.info.get('memory_info') else 0.0
                win_title = window_titles.get(pid, "")

                # Keep the instance with the highest memory / window title
                item = {
                    "pid": pid,
                    "name": name,
                    "window_title": win_title,
                    "memory_mb": mem_mb,
                    "status": proc.info.get('status', 'running'),
                }

                if name not in apps_by_name or (win_title and not apps_by_name[name]["window_title"]) or mem_mb > apps_by_name[name]["memory_mb"]:
                    apps_by_name[name] = item

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        result_list = list(apps_by_name.values())
        result_list.sort(key=lambda x: x["memory_mb"], reverse=True)
        return result_list

    @staticmethod
    def close_app(app_identifier: str, graceful_timeout_sec: float = 3.0) -> Dict[str, Any]:
        """
        Gracefully close an application by process name or PID.
        Sends termination request and waits up to graceful_timeout_sec.
        """
        targets = AppManager._find_processes(app_identifier)
        if not targets:
            return {
                "closed": False,
                "target": app_identifier,
                "error": f"No running process found matching '{app_identifier}'.",
            }

        closed_pids: List[int] = []
        failed_pids: List[int] = []

        for proc in targets:
            try:
                pid = proc.pid
                proc.terminate()
                closed_pids.append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                failed_pids.append(proc.pid)

        # Wait briefly for termination
        gone, alive = psutil.wait_procs(targets, timeout=graceful_timeout_sec)

        return {
            "closed": len(closed_pids) > 0,
            "target": app_identifier,
            "terminated_pids": closed_pids,
            "still_alive_pids": [p.pid for p in alive],
            "status": f"Gracefully closed {len(gone)} instance(s) of '{app_identifier}'.",
        }

    @staticmethod
    def force_kill_app(app_identifier: str) -> Dict[str, Any]:
        """
        Strictly force-kill an application and its child processes.
        Reserved for STRICT security tier.
        """
        targets = AppManager._find_processes(app_identifier)
        if not targets:
            return {
                "killed": False,
                "target": app_identifier,
                "error": f"No running process found matching '{app_identifier}'.",
            }

        killed_pids: List[int] = []
        for proc in targets:
            try:
                # Kill children first, then parent
                for child in proc.children(recursive=True):
                    try:
                        child.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                proc.kill()
                killed_pids.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return {
            "killed": len(killed_pids) > 0,
            "target": app_identifier,
            "killed_pids": killed_pids,
            "status": f"Force terminated {len(killed_pids)} process(es) matching '{app_identifier}'.",
        }

    @staticmethod
    def _find_processes(identifier: str) -> List[psutil.Process]:
        """Helper to find processes matching an integer PID or case-insensitive name."""
        matches: List[psutil.Process] = []
        clean_id = identifier.strip().lower()

        # If identifier is numeric PID
        if clean_id.isdigit():
            try:
                matches.append(psutil.Process(int(clean_id)))
                return matches
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return []

        # Resolve alias if known
        alias_name = KNOWN_APP_ALIASES.get(clean_id, clean_id)
        search_names = {clean_id, alias_name}
        if not clean_id.endswith(".exe"):
            search_names.add(f"{clean_id}.exe")
        if not alias_name.endswith(".exe"):
            search_names.add(f"{alias_name}.exe")

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info['name'].lower()
                if pname in search_names or any(s in pname for s in search_names):
                    matches.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return matches

    @staticmethod
    def get_system_vitals() -> Dict[str, Any]:
        """
        Get real-time CPU, RAM, Disk, and Battery diagnostics.
        Tier: 🟢 SAFE
        """
        cpu_pct = psutil.cpu_percent(interval=0.2)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")

        battery_info = None
        if hasattr(psutil, "sensors_battery"):
            bat = psutil.sensors_battery()
            if bat:
                battery_info = {
                    "percent": bat.percent,
                    "power_plugged": bat.power_plugged,
                    "secs_left": bat.secsleft if bat.secsleft != psutil.POWER_TIME_UNLIMITED else "Plugged In",
                }

        return {
            "success": True,
            "cpu_percent": cpu_pct,
            "memory": {
                "total_gb": round(mem.total / (1024 ** 3), 1),
                "used_gb": round(mem.used / (1024 ** 3), 1),
                "available_gb": round(mem.available / (1024 ** 3), 1),
                "percent_used": mem.percent,
            },
            "disk_c": {
                "total_gb": round(disk.total / (1024 ** 3), 1),
                "free_gb": round(disk.free / (1024 ** 3), 1),
                "percent_used": disk.percent,
            },
            "battery": battery_info,
            "status": f"CPU: {cpu_pct}% | RAM: {mem.percent}% | Disk C: {disk.percent}% used" + (f" | Battery: {battery_info['percent']}%" if battery_info else ""),
        }

    @staticmethod
    def get_clipboard() -> Dict[str, Any]:
        """
        Read current text contents from Windows clipboard.
        Tier: 🟢 SAFE
        """
        try:
            cmd = ["powershell", "-NoProfile", "-Command", "Get-Clipboard"]
            out = subprocess.check_output(cmd, text=True, timeout=3)
            return {
                "success": True,
                "text": out.rstrip("\r\n"),
                "status": "Retrieved clipboard text.",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get clipboard: {str(e)}"}

    @staticmethod
    def set_clipboard(text: str) -> Dict[str, Any]:
        """
        Write text to Windows clipboard.
        Tier: 🟢 SAFE
        """
        try:
            # Pass text safely through stdin to clip.exe
            process = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=text, timeout=3)
            return {
                "success": True,
                "length": len(text),
                "status": f"Copied {len(text)} characters to clipboard.",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to set clipboard: {str(e)}"}

    @staticmethod
    def minimize_all_windows() -> Dict[str, Any]:
        """
        Toggle show desktop / minimize all windows (Win + D).
        Tier: 🟢 SAFE
        """
        import ctypes
        user32 = ctypes.windll.user32
        VK_LWIN = 0x5B
        VK_D = 0x44
        KEYEVENTF_KEYUP = 0x0002

        user32.keybd_event(VK_LWIN, 0, 0, 0)
        user32.keybd_event(VK_D, 0, 0, 0)
        user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

        return {
            "success": True,
            "status": "Minimized all windows (Show Desktop).",
        }

    @staticmethod
    def send_hotkey(hotkey: str) -> Dict[str, Any]:
        """
        Trigger standard keyboard shortcuts like 'ctrl+s', 'alt+tab', 'ctrl+w', 'win+d'.
        Tier: 🟡 CONFIRM
        """
        import ctypes
        user32 = ctypes.windll.user32
        KEYEVENTF_KEYUP = 0x0002

        KEY_CODES = {
            "ctrl": 0x11,
            "alt": 0x12,
            "shift": 0x10,
            "win": 0x5B,
            "tab": 0x09,
            "esc": 0x1B,
            "enter": 0x0D,
            "space": 0x20,
            "s": 0x53,
            "c": 0x43,
            "v": 0x56,
            "w": 0x57,
            "d": 0x44,
            "f": 0x46,
            "t": 0x54,
            "f11": 0x7A,
        }

        keys = [k.strip().lower() for k in hotkey.split("+")]
        vk_list = [KEY_CODES.get(k) for k in keys if KEY_CODES.get(k)]

        if not vk_list:
            return {"success": False, "error": f"Unsupported hotkey combinations: '{hotkey}'"}

        # Press keys down in order
        for vk in vk_list:
            user32.keybd_event(vk, 0, 0, 0)

        # Release keys in reverse order
        for vk in reversed(vk_list):
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

        return {
            "success": True,
            "hotkey": hotkey,
            "status": f"Sent keyboard hotkey: {hotkey.upper()}",
        }

