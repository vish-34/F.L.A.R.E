"""
Windows File & Application Search Tools.
Provides fast search capabilities across common Windows directories and Start Menu shortcuts.
Tier: 🟢 SAFE (read-only discovery).
"""

import fnmatch
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

# Directories to skip to preserve performance and prevent infinite loops
EXCLUDED_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "$recycle.bin",
    "system volume information",
    "appdata\\local\\temp",
    ".cargo",
    ".rustup",
    ".cache",
}


class WindowsSearch:
    """Fast search engine for files and installed applications on Windows."""

    @staticmethod
    def get_common_user_dirs() -> Dict[str, Path]:
        """Return paths to standard Windows user directories."""
        home = Path.home()
        return {
            "Desktop": home / "Desktop",
            "Documents": home / "Documents",
            "Downloads": home / "Downloads",
            "Pictures": home / "Pictures",
            "Videos": home / "Videos",
            "Music": home / "Music",
            "Home": home,
        }

    @classmethod
    def search_files(
        cls,
        query: str,
        search_root: Optional[str] = None,
        max_results: int = 25,
        max_depth: int = 5,
        extension: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for files matching query string or glob pattern.
        """
        results: List[Dict[str, Any]] = []
        clean_query = query.strip()
        is_glob = any(char in clean_query for char in ["*", "?", "[", "]"])

        if search_root:
            roots = [Path(search_root).resolve()]
        else:
            user_dirs = cls.get_common_user_dirs()
            # Prioritize Desktop, Documents, Downloads, then current workspace
            roots = [
                Path.cwd(),
                user_dirs["Documents"],
                user_dirs["Desktop"],
                user_dirs["Downloads"],
            ]

        # Normalize extension filter
        ext_filter = extension.lower() if extension else None
        if ext_filter and not ext_filter.startswith("."):
            ext_filter = f".{ext_filter}"

        seen_paths = set()

        for root_path in roots:
            if not root_path.exists() or not root_path.is_dir():
                continue

            root_depth = len(root_path.parts)

            for dirpath, dirnames, filenames in os.walk(str(root_path)):
                # Prune excluded directories
                current_dir = Path(dirpath)
                current_depth = len(current_dir.parts) - root_depth
                if current_depth >= max_depth:
                    dirnames.clear()
                    continue

                dirnames[:] = [
                    d for d in dirnames
                    if d.lower() not in EXCLUDED_DIRS
                    and not d.startswith("$")
                    and not (current_dir / d).is_symlink()
                ]

                for fname in filenames:
                    # Check extension if specified
                    if ext_filter and not fname.lower().endswith(ext_filter):
                        continue

                    # Match query
                    matched = False
                    if is_glob:
                        matched = fnmatch.fnmatch(fname.lower(), clean_query.lower())
                    else:
                        matched = clean_query.lower() in fname.lower()

                    if matched:
                        file_path = current_dir / fname
                        resolved_str = str(file_path.resolve())
                        if resolved_str in seen_paths:
                            continue
                        seen_paths.add(resolved_str)

                        try:
                            stat = file_path.stat()
                            results.append({
                                "name": fname,
                                "path": resolved_str,
                                "size_bytes": stat.st_size,
                                "size_kb": round(stat.st_size / 1024, 1),
                                "is_dir": False,
                                "modified": stat.st_mtime,
                            })
                        except (PermissionError, OSError):
                            results.append({
                                "name": fname,
                                "path": resolved_str,
                                "is_dir": False,
                                "size_bytes": 0,
                                "size_kb": 0,
                            })

                        if len(results) >= max_results:
                            return results

        return results

    @staticmethod
    def find_installed_app(app_name: str) -> List[Dict[str, Any]]:
        """
        Locate installed applications by searching PATH, Start Menu, and App directories.
        """
        clean_name = app_name.strip().lower()
        found: List[Dict[str, Any]] = []
        seen_targets = set()

        # 1. Check system PATH via shutil.which
        which_path = shutil.which(clean_name)
        if which_path:
            found.append({
                "name": Path(which_path).name,
                "path": which_path,
                "source": "PATH",
            })
            seen_targets.add(which_path.lower())

        # 2. Check Windows Start Menu folders for shortcuts (.lnk)
        start_menu_paths = [
            Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs",
            Path(os.environ.get("ProgramData", r"C:\ProgramData")) / r"Microsoft\Windows\Start Menu\Programs",
            Path.home() / r"AppData\Local\Programs",
        ]

        for base_folder in start_menu_paths:
            if not base_folder.exists():
                continue

            for dirpath, _, filenames in os.walk(str(base_folder)):
                for fname in filenames:
                    f_lower = fname.lower()
                    if clean_name in f_lower:
                        full_p = Path(dirpath) / fname
                        p_str = str(full_p.resolve())
                        if p_str.lower() not in seen_targets:
                            seen_targets.add(p_str.lower())
                            found.append({
                                "name": fname,
                                "path": p_str,
                                "source": "StartMenu / Programs",
                            })
                        if len(found) >= 10:
                            return found

        return found

    @staticmethod
    def read_file_preview(file_path: str, max_lines: int = 50) -> Dict[str, Any]:
        """
        Safely preview the first max_lines of a file.
        """
        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            return {"error": f"File not found: {file_path}", "lines": []}
        if not path_obj.is_file():
            return {"error": f"Path is not a file: {file_path}", "lines": []}

        # Check size to prevent memory bloat (max 5MB preview)
        if path_obj.stat().st_size > 5 * 1024 * 1024:
            return {
                "error": "File exceeds 5MB preview limit.",
                "size_mb": round(path_obj.stat().st_size / (1024 * 1024), 2),
            }

        lines = []
        try:
            with open(path_obj, "r", encoding="utf-8", errors="replace") as f:
                for idx, line in enumerate(f, start=1):
                    lines.append(line.rstrip("\r\n"))
                    if idx >= max_lines:
                        break
            return {
                "file": str(path_obj),
                "total_lines_read": len(lines),
                "lines": lines,
            }
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}", "lines": []}
