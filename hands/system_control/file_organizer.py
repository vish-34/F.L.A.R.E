"""
Smart File Organizer for F.L.A.R.E Hands.
Cleanly organizes messy folders (Downloads, Desktop) into categorized subfolders.
"""

from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

EXTENSIONS_MAP = {
    "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".txt", ".csv", ".epub"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
    "Installers": [".exe", ".msi", ".iso"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".cpp", ".java", ".sql"],
}


class FileOrganizer:
    """Safely organizes directory files into categorized groups."""

    @classmethod
    def organize_directory(
        cls,
        target_directory: str = "downloads",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Organize files in the specified directory into categorized folders.
        Tier: 🟡 CONFIRM
        """
        home = Path.home()
        if target_directory.lower() == "downloads":
            target_path = home / "Downloads"
        elif target_directory.lower() == "desktop":
            target_path = home / "Desktop"
        elif target_directory.lower() in ["workspace", "current", "project"]:
            target_path = Path.cwd()
        else:
            target_path = Path(target_directory).resolve()

        if not target_path.exists() or not target_path.is_dir():
            return {"success": False, "error": f"Directory not found: {target_path}"}

        # Invert mapping for quick lookup: ext -> category
        ext_to_cat = {}
        for category, exts in EXTENSIONS_MAP.items():
            for ext in exts:
                ext_to_cat[ext.lower()] = category

        moved_files: List[Dict[str, str]] = []
        skipped_files: List[str] = []

        for item in target_path.iterdir():
            if item.is_dir():
                continue  # Skip existing folders

            ext = item.suffix.lower()
            category = ext_to_cat.get(ext)

            if category:
                dest_folder = target_path / category
                dest_file = dest_folder / item.name

                # Handle name collision by appending counter
                if not dry_run:
                    dest_folder.mkdir(exist_ok=True)
                    if dest_file.exists():
                        counter = 1
                        while (dest_folder / f"{item.stem}_{counter}{item.suffix}").exists():
                            counter += 1
                        dest_file = dest_folder / f"{item.stem}_{counter}{item.suffix}"

                    try:
                        shutil.move(str(item), str(dest_file))
                        moved_files.append({
                            "file": item.name,
                            "category": category,
                            "dest": str(dest_file),
                        })
                    except Exception as e:
                        skipped_files.append(f"{item.name} ({str(e)})")
                else:
                    moved_files.append({
                        "file": item.name,
                        "category": category,
                        "dest": str(dest_file),
                    })
            else:
                skipped_files.append(item.name)

        return {
            "success": True,
            "target_directory": str(target_path),
            "dry_run": dry_run,
            "total_organized": len(moved_files),
            "total_skipped": len(skipped_files),
            "moves": moved_files[:30],  # Return first 30 for brevity
            "status": f"{'[DRY RUN] Would organize' if dry_run else 'Successfully organized'} {len(moved_files)} files in {target_path.name}.",
        }
