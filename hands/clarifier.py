"""
Interactive Dialogue Clarifier for F.L.A.R.E Hands.
Engages in polite clarifying dialogue when user instructions are underspecified.
"""

from pathlib import Path
import re
from typing import Any, Callable, Dict, Optional


class TaskClarifier:
    """Interactively clarifies missing task parameters."""

    @staticmethod
    def clarify_coding_task(
        user_prompt: str,
        input_func: Optional[Callable[[str], str]] = None,
    ) -> Dict[str, Any]:
        """
        Ask clarifying questions for a script creation request if details are missing.
        """
        prompt_input = input_func or input

        print("\n" + "=" * 55)
        print("🤖 FLARE DEVELOPER ASSISTANT: Clarification Dialogue")
        print("=" * 55)

        # 1. Determine script filename or purpose
        filename = "script.py"
        # Try to infer from prompt
        words = user_prompt.lower()
        if "fibonacci" in words:
            filename = "fibonacci.py"
        elif "download" in words or "youtube" in words:
            filename = "yt_downloader.py"
        elif "scraper" in words or "scrape" in words:
            filename = "scraper.py"
        elif "organize" in words or "clean" in words:
            filename = "file_cleaner.py"

        # Ask user for filename confirmation
        custom_file = prompt_input(f"📄 Script Filename [Default: {filename}]: ").strip()
        if custom_file:
            filename = custom_file if custom_file.endswith(".py") else f"{custom_file}.py"

        # 2. Ask for destination directory
        print("\n📁 Where should I save the script?")
        print("   1. Current Workspace (F.L.A.R.E root)")
        print("   2. Desktop")
        print("   3. Documents")
        dir_choice = prompt_input("Choose [1/2/3, Default: 1]: ").strip()

        dest_dir = "workspace"
        if dir_choice == "2" or "desktop" in dir_choice.lower():
            dest_dir = "desktop"
        elif dir_choice == "3" or "doc" in dir_choice.lower():
            dest_dir = "documents"

        # 3. Ask for preferred editor
        print("\n💻 Which editor would you like me to open it in?")
        print("   1. VS Code ('code')")
        print("   2. Notepad")
        print("   3. None (just save the file)")
        editor_choice = prompt_input("Choose [1/2/3, Default: 1]: ").strip()

        chosen_editor = "code"
        if editor_choice == "2" or "notepad" in editor_choice.lower():
            chosen_editor = "notepad"
        elif editor_choice == "3" or "none" in editor_choice.lower():
            chosen_editor = None

        print("=" * 55 + "\n")

        return {
            "filename": filename,
            "target_directory": dest_dir,
            "open_in_editor": chosen_editor,
        }
