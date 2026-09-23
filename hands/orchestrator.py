"""
Hands Action Orchestrator for F.L.A.R.E.
Translates human natural language goals into concrete tool execution and multi-turn workflows.
Combines sub-5ms rule-based fast dispatch with LLM reasoning.
"""

import re
import time
from typing import Any, Dict, Optional

from hands.clarifier import TaskClarifier
from hands.registry import ToolRegistry


class HandsOrchestrator:
    """Dispatches natural language instructions to guarded tool actions."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()

    def handle_natural_input(self, user_text: str) -> Dict[str, Any]:
        """
        Parse human intent and execute corresponding hands action.
        """
        text = user_text.strip()
        lower = text.lower()

        # 1. Chained Timed App Commands (e.g. 'open notepad and close it after 3 sec')
        timed_match = re.search(
            r"open\s+([a-zA-Z0-9_\-]+)\s+and\s+close\s+(?:it\s+)?after\s+(\d+)\s*(?:sec|seconds|s)?",
            lower,
        )
        if timed_match:
            app_target = timed_match.group(1).strip()
            delay_sec = int(timed_match.group(2))
            open_res = self.registry.execute("open_app", app_identifier=app_target)
            if not open_res.get("success"):
                return {
                    "handled": True,
                    "intent": "open_and_close_timed",
                    "result": open_res,
                    "message": f"Failed to open '{app_target}': {open_res.get('error')}",
                }
            print(f"\n⏳ Waiting {delay_sec} second(s) before closing '{app_target}'...")
            time.sleep(delay_sec)
            close_res = self.registry.execute("close_app", app_identifier=app_target)
            return {
                "handled": True,
                "intent": "open_and_close_timed",
                "result": {"open": open_res, "close": close_res},
                "message": f"Opened '{app_target}', waited {delay_sec} seconds, and gracefully closed it.",
            }

        # 2. Chained Browser & Play Media Commands (e.g. 'open brave and play loser by dino james')
        browser_play_match = re.search(
            r"^(?:please\s+)?(?:open|launch)\s+(brave|chrome|edge)\s+(?:and|to)\s+play\s+(.+)$",
            lower,
        )
        if browser_play_match:
            browser = browser_play_match.group(1).strip()
            media_query = browser_play_match.group(2).strip()
            platform = "youtube"
            if "on spotify" in media_query:
                platform = "spotify"
                media_query = media_query.replace("on spotify", "").strip()
            elif "on youtube" in media_query:
                platform = "youtube"
                media_query = media_query.replace("on youtube", "").strip()

            result = self.registry.execute("play_media", query=media_query, platform=platform, browser=browser)
            return {
                "handled": True,
                "intent": "play_media",
                "result": result,
                "message": f"Playing '{media_query}' on {platform.title()} via {browser.title()}.",
            }

        # 3. Browser Search Chained Commands (e.g. 'open brave and search youtube')
        browser_search_match = re.search(r"open\s+(brave|chrome|edge)\s+and\s+search\s+(.+)$", lower)
        if browser_search_match:
            browser = browser_search_match.group(1).strip()
            query = browser_search_match.group(2).strip()
            if "youtube" in query:
                sq = query.replace("youtube", "").replace("for", "").replace("on", "").strip() or "trending music"
                result = self.registry.execute("play_media", query=sq, platform="youtube", browser=browser)
                return {
                    "handled": True,
                    "intent": "play_media",
                    "result": result,
                    "message": f"Opened {browser.title()} and searched YouTube for '{sq}'.",
                }
            else:
                result = self.registry.execute("search_web_and_open", query=query, engine="brave", browser=browser)
                return {
                    "handled": True,
                    "intent": "web_search",
                    "result": result,
                    "message": f"Opened {browser.title()} and searched for '{query}'.",
                }

        # 4. Media Playback Intent (e.g. 'play loser by dino james', 'play eminem without me')
        play_match = re.search(r"^(?:please\s+)?(?:play|listen to)\s+(.+)$", lower)
        if play_match:
            media_query = play_match.group(1).strip()
            platform = "youtube"
            browser = "brave"
            if "in chrome" in media_query or "on chrome" in media_query:
                browser = "chrome"
                media_query = re.sub(r"\s*(?:in|on)\s+chrome", "", media_query).strip()
            elif "in brave" in media_query or "on brave" in media_query:
                browser = "brave"
                media_query = re.sub(r"\s*(?:in|on)\s+brave", "", media_query).strip()

            if "on spotify" in media_query:
                platform = "spotify"
                media_query = media_query.replace("on spotify", "").strip()
            elif "on youtube" in media_query:
                platform = "youtube"
                media_query = media_query.replace("on youtube", "").strip()

            result = self.registry.execute("play_media", query=media_query, platform=platform, browser=browser)
            return {
                "handled": True,
                "intent": "play_media",
                "result": result,
                "message": f"Playing '{media_query}' on {platform.title()} via {browser.title()}.",
            }

        # 4. Desktop & Screen Minimization Variations
        if any(phrase in lower for phrase in [
            "show me desktop", "show desktop", "go to desktop", "to desktop",
            "minimize the screen", "minimize screen", "minimize all", "minimize windows",
        ]) or lower == "desktop":
            result = self.registry.execute("minimize_all_windows")
            return {
                "handled": True,
                "intent": "minimize_all",
                "result": result,
                "message": "Minimized all windows (Desktop shown).",
            }

        # 4b. Task View: Show all open apps in small windows (3-finger gesture / Win+Tab)
        if any(phrase in lower for phrase in [
            "show me all apps open", "show all apps open", "show all apps", "show me all apps",
            "show all windows", "show me all windows", "task view", "all open apps",
            "overview of apps", "overview of all apps", "pull up all apps"
        ]):
            result = self.registry.execute("show_task_view")
            return {
                "handled": True,
                "intent": "show_task_view",
                "result": result,
                "message": result.get("data", {}).get("status", "Opened Windows Task View (All open apps displayed in small windows)."),
            }

        # 4c. List open apps
        if lower in ["list", "list apps", "list all apps", "what apps are open", "show running apps", "running apps", "open apps", "apps"]:
            result = self.registry.execute("format_running_apps")
            return {
                "handled": True,
                "intent": "list_apps",
                "result": result,
                "message": result.get("data", {}).get("status", "Listed running applications."),
            }

        # 4d. Switch to app and full-screen it (minimize rest)
        switch_app_match = re.match(r"^(?:please\s+)?(?:switch\s+to|focus|bring\s+up|maximize)\s+([a-zA-Z0-9_\-\s]+)$", lower)
        if switch_app_match and not any(w in lower for w in ["tab", "window"]):
            app_target = switch_app_match.group(1).strip()
            result = self.registry.execute("switch_and_fullscreen_app", app_identifier=app_target, minimize_others=True)
            return {
                "handled": True,
                "intent": "switch_and_fullscreen_app",
                "result": result,
                "message": result.get("data", {}).get("status") or f"Switched to '{app_target}' in full screen.",
            }

        # 5. Tab & Window Navigation (e.g. 'switch tabs', 'next tab', 'switch window')
        if any(phrase in lower for phrase in ["switch tab", "switch tabs", "next tab", "change tab"]):
            result = self.registry.execute("switch_tab", direction="next")
            return {
                "handled": True,
                "intent": "switch_tab",
                "result": result,
                "message": "Switched to next tab (Ctrl+Tab).",
            }

        if any(phrase in lower for phrase in ["prev tab", "previous tab"]):
            result = self.registry.execute("switch_tab", direction="prev")
            return {
                "handled": True,
                "intent": "prev_tab",
                "result": result,
                "message": "Switched to previous tab (Ctrl+Shift+Tab).",
            }

        if any(phrase in lower for phrase in ["close tab"]):
            result = self.registry.execute("close_tab")
            return {
                "handled": True,
                "intent": "close_tab",
                "result": result,
                "message": "Closed active tab (Ctrl+W).",
            }

        if any(phrase in lower for phrase in ["new tab"]):
            result = self.registry.execute("new_tab")
            return {
                "handled": True,
                "intent": "new_tab",
                "result": result,
                "message": "Opened new tab (Ctrl+T).",
            }

        if any(phrase in lower for phrase in ["switch window", "switch windows", "alt tab", "next window"]):
            result = self.registry.execute("switch_window")
            return {
                "handled": True,
                "intent": "switch_window",
                "result": result,
                "message": "Switched window (Alt+Tab).",
            }

        # 6. Volume Controls
        vol_match = re.search(r"volume\s+(?:to\s+)?(\d{1,3})%?", lower)
        if vol_match:
            level = int(vol_match.group(1))
            result = self.registry.execute("set_volume", level_percent=level)
            return {
                "handled": True,
                "intent": "set_volume",
                "result": result,
                "message": f"Master volume set to {level}%.",
            }

        if "volume up" in lower or "turn up the volume" in lower:
            result = self.registry.execute("adjust_volume", direction="up", steps=5)
            return {"handled": True, "intent": "adjust_volume", "result": result, "message": "Turned volume up."}

        if "volume down" in lower or "turn down the volume" in lower:
            result = self.registry.execute("adjust_volume", direction="down", steps=5)
            return {"handled": True, "intent": "adjust_volume", "result": result, "message": "Turned volume down."}

        if "mute" in lower:
            result = self.registry.execute("toggle_mute")
            return {"handled": True, "intent": "toggle_mute", "result": result, "message": "Toggled audio mute."}

        # 7. System Vitals & Health
        if any(w in lower for w in ["vitals", "health", "how is my pc", "pc stats", "system stats", "battery status"]):
            result = self.registry.execute("get_system_vitals")
            return {
                "handled": True,
                "intent": "system_vitals",
                "result": result,
                "message": result.get("data", {}).get("status", "System vitals retrieved."),
            }

        # 8. Screenshots
        if "screenshot" in lower or "screen capture" in lower:
            result = self.registry.execute("take_screenshot")
            return {
                "handled": True,
                "intent": "take_screenshot",
                "result": result,
                "message": result.get("data", {}).get("status", "Screenshot captured."),
            }

        # 9. Clean / Organize Folders
        if "organize" in lower or "clean downloads" in lower or "clean desktop" in lower:
            target = "desktop" if "desktop" in lower else "downloads"
            dry_run = "preview" in lower or "dry run" in lower
            result = self.registry.execute("organize_directory", target_directory=target, dry_run=dry_run)
            return {
                "handled": True,
                "intent": "organize_directory",
                "result": result,
                "message": result.get("data", {}).get("status", f"Organized {target}."),
            }

        # 10. Interactive Developer Script & Code Writing
        # Hands script creation is for creating a runnable script/file on disk.
        # Conversational questions asking for small snippets/functions (e.g. "write a python function to reverse a string")
        # remain in conversational chat instead of prompting for file creation.
        is_function_or_snippet = any(word in lower for word in ["function", "snippet", "regex", "example", "how do i", "how to"])
        coding_triggers = [
            "write script", "write a script", "create script", "create a script",
            "make script", "make a script", "generate script", "build script",
            "new script", "write python script", "write a python script",
            "write code to", "write python code to", "write me code to",
            "code to", "script to", "script for", "code for",
            "create a python program", "write a program to", "write a bot",
        ]
        is_coding_request = (
            not is_function_or_snippet
            and (
                any(trig in lower for trig in coding_triggers)
                or lower in ["code", "script", "python script", "python code", "write script", "create script"]
                or (lower.startswith(("write me", "code me", "create a script", "write python script")) and any(s in lower for s in ["script", "downloader", "scraper", "bot", "tool", "program"]))
            )
            and not lower.startswith(("open code", "launch code", "start code", "close code", "kill code"))
        )

        if is_coding_request:
            clarified = TaskClarifier.clarify_coding_task(text)
            fn = clarified["filename"]
            task_prompt = clarified.get("task_description") or text

            # Try generating real implementation code via Brain's Groq / Provider Mesh
            code_body = None
            try:
                import os
                import litellm
                from dotenv import load_dotenv
                load_dotenv()
                if os.environ.get("GROQ_API_KEY"):
                    print("🧠 [Flare Brain] Synthesizing custom Python code...")
                    llm_res = litellm.completion(
                        model="groq/openai/gpt-oss-120b",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert Python software engineer. Write clean, complete, working Python code. "
                                    "Do NOT wrap in markdown backticks or explanations. Output ONLY pure executable Python code."
                                ),
                            },
                            {
                                "role": "user",
                                "content": f"Write a complete, working Python script for the following task: {task_prompt}",
                            },
                        ],
                        max_tokens=1000,
                        timeout=15,
                    )
                    raw_code = llm_res.choices[0].message.content.strip()
                    # Strip any markdown code blocks if model included them
                    if raw_code.startswith("```"):
                        lines = raw_code.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        raw_code = "\n".join(lines).strip()
                    code_body = raw_code
            except Exception:
                pass

            if not code_body:
                code_body = f'''"""
Automated script generated by F.L.A.R.E.
Task: {text}
"""

def main():
    print("F.L.A.R.E Script '{fn}' initialized.")
    # Add your custom business logic below
    print("Execution complete.")

if __name__ == "__main__":
    main()
'''

            result = self.registry.execute(
                "create_script",
                filename=clarified["filename"],
                code_content=code_body,
                target_directory=clarified["target_directory"],
                open_in_editor=clarified["open_in_editor"],
            )

            return {
                "handled": True,
                "intent": "create_script",
                "result": result,
                "message": result.get("data", {}).get("status", f"Created script '{fn}'."),
            }

        # 11. Simple App Launch fallback (supports 'open', 'launch', 'start')
        open_match = re.match(r"^(?:please\s+)?(?:open|launch|start)\s+([a-zA-Z0-9_\-\s]+)$", lower)
        if open_match:
            raw_target = open_match.group(1).strip()
            # Normalize common multi-word aliases
            alias_map = {
                "brave browser": "brave",
                "chrome browser": "chrome",
                "vs code": "code",
                "visual studio code": "code",
                "task manager": "taskmgr",
                "file explorer": "explorer",
                "calculator": "calc",
            }
            app_target = alias_map.get(raw_target, raw_target)
            result = self.registry.execute("open_app", app_identifier=app_target)
            return {
                "handled": True,
                "intent": "open_app",
                "result": result,
                "message": f"Opened '{app_target}'.",
            }

        # 12. Simple App Close fallback (supports 'close', 'exit', 'quit', 'kill')
        close_match = re.match(r"^(?:please\s+)?(?:close|exit|quit|kill)\s+([a-zA-Z0-9_\-\s]+)$", lower)
        if close_match:
            raw_target = close_match.group(1).strip()
            alias_map = {
                "brave browser": "brave",
                "chrome browser": "chrome",
                "vs code": "code",
                "visual studio code": "code",
                "task manager": "taskmgr",
                "file explorer": "explorer",
                "calculator": "calc",
            }
            app_target = alias_map.get(raw_target, raw_target)
            result = self.registry.execute("close_app", app_identifier=app_target)
            return {
                "handled": True,
                "intent": "close_app",
                "result": result,
                "message": f"Closed '{app_target}'.",
            }

        # 13. Web Search fallback
        search_match = re.search(r"search\s+(?:for\s+)?(.+?)(?:\s+on\s+(google|brave|github|reddit|youtube))?$", lower)
        if search_match:
            sq = search_match.group(1).strip()
            eng = search_match.group(2) or "brave"
            result = self.registry.execute("search_web_and_open", query=sq, engine=eng, browser="brave")
            return {
                "handled": True,
                "intent": "web_search",
                "result": result,
                "message": f"Searched '{sq}' on {eng.title()} via Brave.",
            }

        return {
            "handled": False,
            "intent": "unknown",
            "message": "I didn't recognize that specific action pattern. Type 'help' to see available tools.",
        }
