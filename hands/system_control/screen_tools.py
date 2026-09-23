"""
Screen Vision and Screenshot Capture Tools for F.L.A.R.E Hands.
Uses native Windows .NET graphics to capture screenshots without requiring external dependencies.
"""

from datetime import datetime
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, Optional


class ScreenTools:
    """Takes screenshots and inspects screen display context."""

    @staticmethod
    def take_screenshot(
        filename: Optional[str] = None,
        target_directory: str = "pictures",
    ) -> Dict[str, Any]:
        """
        Capture the current desktop screen and save as PNG.
        Tier: 🟢 SAFE
        """
        home = Path.home()
        if target_directory.lower() == "pictures":
            dest_dir = home / "Pictures"
        elif target_directory.lower() == "desktop":
            dest_dir = home / "Desktop"
        else:
            dest_dir = Path(target_directory).resolve()

        dest_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flare_screenshot_{ts}.png"
        elif not filename.lower().endswith(".png"):
            filename = f"{filename}.png"

        save_path = (dest_dir / filename).resolve()

        # PowerShell one-liner using System.Drawing to capture the primary screen
        ps_cmd = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{str(save_path)}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
"""
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                check=True,
                capture_output=True,
                timeout=6,
            )
            if save_path.exists():
                return {
                    "success": True,
                    "file_path": str(save_path),
                    "filename": filename,
                    "size_kb": round(save_path.stat().st_size / 1024, 1),
                    "status": f"Screenshot saved successfully at {save_path}.",
                }
            else:
                return {
                    "success": False,
                    "error": "Screenshot file was not created.",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to capture screen: {str(e)}",
            }
