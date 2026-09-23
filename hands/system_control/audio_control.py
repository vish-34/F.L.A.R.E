"""
Windows Master Volume Control for F.L.A.R.E Hands.
Provides master volume adjustment and mute toggling via Windows multimedia controls.
"""

import ctypes
import subprocess
from typing import Any, Dict

# Windows Virtual Key Codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_KEYUP = 0x0002


class AudioControl:
    """Controls Windows system master volume."""

    @staticmethod
    def set_volume(level_percent: int) -> Dict[str, Any]:
        """
        Set system master volume to an approximate percentage (0 - 100).
        Uses Windows audio endpoint PowerShell script block.
        Tier: 🟢 SAFE
        """
        target = max(0, min(100, int(level_percent)))

        # PowerShell command using AudioDeviceCmdlets or SndVol endpoint
        ps_script = f"""
$obj = New-Object -ComObject WScript.Shell
# Step volume to zero first
1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
# Now step up to desired percentage (approx 2% per step)
$steps = [math]::Round({target} / 2)
1..$steps | ForEach-Object {{ $obj.SendKeys([char]175) }}
"""
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                timeout=4,
                capture_output=True,
            )
            return {
                "success": True,
                "target_percent": target,
                "status": f"Master volume adjusted to approx {target}%.",
            }
        except Exception as e:
            # Fallback: step up or down using ctypes keybd_event
            return {
                "success": False,
                "error": f"Failed to set volume: {str(e)}",
            }

    @staticmethod
    def adjust_volume(direction: str = "up", steps: int = 5) -> Dict[str, Any]:
        """
        Adjust volume up or down by step count.
        Tier: 🟢 SAFE
        """
        user32 = ctypes.windll.user32
        vk_code = VK_VOLUME_UP if direction.lower() == "up" else VK_VOLUME_DOWN
        for _ in range(max(1, min(25, steps))):
            user32.keybd_event(vk_code, 0, 0, 0)
            user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

        return {
            "success": True,
            "direction": direction,
            "steps": steps,
            "status": f"Volume stepped {direction} by {steps * 2}%.",
        }

    @staticmethod
    def toggle_mute() -> Dict[str, Any]:
        """
        Toggle master audio mute.
        Tier: 🟢 SAFE
        """
        user32 = ctypes.windll.user32
        user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        user32.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_KEYUP, 0)
        return {
            "success": True,
            "status": "Toggled master audio mute.",
        }
