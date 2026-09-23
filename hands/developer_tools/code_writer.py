"""
Developer Code Writer Studio for F.L.A.R.E Hands.
Creates syntax-validated script files and launches them in user-preferred editors.
"""

import ast
import os
from pathlib import Path
from typing import Any, Dict, Optional


class CodeWriter:
    """Safely generates, syntax-checks, and saves script files."""

    @classmethod
    def resolve_directory(cls, dir_identifier: Optional[str]) -> Path:
        """Resolve a directory nickname or path."""
        home = Path.home()
        if not dir_identifier or dir_identifier.lower() in ["workspace", "project", "current"]:
            return Path.cwd()
        elif dir_identifier.lower() == "desktop":
            return home / "Desktop"
        elif dir_identifier.lower() in ["documents", "docs"]:
            return home / "Documents"
        elif dir_identifier.lower() in ["downloads"]:
            return home / "Downloads"
        else:
            p = Path(dir_identifier).resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p

    @classmethod
    def create_script(
        cls,
        filename: str,
        code_content: str,
        target_directory: str = "workspace",
        open_in_editor: Optional[str] = "code",
    ) -> Dict[str, Any]:
        """
        Create a new script file with syntax validation.
        Tier: 🟡 CONFIRM
        """
        clean_name = filename.strip()
        if not clean_name:
            return {"success": False, "error": "Filename cannot be empty."}

        # Validate Python syntax if file is a .py file
        is_python = clean_name.lower().endswith(".py")
        if is_python:
            try:
                ast.parse(code_content, filename=clean_name)
            except SyntaxError as syn_err:
                return {
                    "success": False,
                    "error": f"Python Syntax Error on line {syn_err.lineno}: {syn_err.msg}",
                    "line": syn_err.lineno,
                    "offset": syn_err.offset,
                }

        # Resolve target directory
        dest_dir = cls.resolve_directory(target_directory)
        dest_dir.mkdir(parents=True, exist_ok=True)
        target_file = (dest_dir / clean_name).resolve()

        # Write file
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(code_content)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file to disk: {str(e)}",
            }

        editor_result = None
        if open_in_editor:
            from hands.system_control.app_manager import AppManager
            ed = open_in_editor.strip().lower()
            editor_result = AppManager.open_app(ed, arguments=str(target_file))

        return {
            "success": True,
            "filename": clean_name,
            "file_path": str(target_file),
            "directory": str(dest_dir),
            "size_bytes": target_file.stat().st_size,
            "opened_in_editor": open_in_editor if (editor_result and editor_result.get("launched")) else None,
            "status": f"Script '{clean_name}' successfully created at {target_file}" + (f" and opened in {open_in_editor}." if open_in_editor else "."),
        }
