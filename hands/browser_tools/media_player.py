"""
Media playback and hardware media key automation for F.L.A.R.E Hands.
Provides direct playback on YouTube/Spotify and Windows multimedia key simulation.
"""

import ctypes
import os
import subprocess
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

# Windows Virtual Key Codes for Media Controls
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

KEYEVENTF_KEYUP = 0x0002


class MediaPlayer:
    """Controls browser media playback and hardware media keys."""

    @staticmethod
    def resolve_youtube_watch_url(query: str) -> str:
        """
        Extract the first matching YouTube video URL to begin direct playback.
        Falls back to standard search page if video ID is not found.
        """
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                html = response.read().decode("utf-8", errors="ignore")
            matches = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
            if not matches:
                matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if matches:
                return f"https://www.youtube.com/watch?v={matches[0]}&autoplay=1"
        except Exception:
            pass
        return search_url

    @staticmethod
    def play_media(
        query: str,
        platform: str = "youtube",
        browser: str = "brave",
    ) -> Dict[str, Any]:
        """
        Play a song, video, or podcast on YouTube or Spotify in the specified browser.
        Tier: 🟡 CONFIRM
        """
        clean_query = query.strip()
        encoded_query = urllib.parse.quote_plus(clean_query)
        platform_lower = platform.strip().lower()

        if "spotify" in platform_lower:
            url = f"https://open.spotify.com/search/{encoded_query}"
        elif "soundcloud" in platform_lower:
            url = f"https://soundcloud.com/search?q={encoded_query}"
        else:
            # Resolve directly to the first playable video on YouTube
            url = MediaPlayer.resolve_youtube_watch_url(clean_query)

        # Resolve browser launcher
        from hands.system_control.app_manager import AppManager
        res = AppManager.open_app(browser, arguments=url)

        if res.get("launched"):
            return {
                "success": True,
                "platform": platform,
                "query": clean_query,
                "url": url,
                "browser": browser,
                "status": f"Now playing '{clean_query}' on {platform.title()} via {browser.title()}.",
            }
        else:
            # Fallback to system default browser via os.startfile
            try:
                os.startfile(url)
                return {
                    "success": True,
                    "platform": platform,
                    "query": clean_query,
                    "url": url,
                    "browser": "default",
                    "status": f"Now playing '{clean_query}' on {platform.title()} via system default browser.",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to open media URL: {str(e)}",
                }

    @staticmethod
    def media_control(action: str) -> Dict[str, Any]:
        """
        Trigger native Windows multimedia keyboard events.
        Actions: 'play_pause', 'next', 'prev', 'stop', 'mute', 'vol_up', 'vol_down'
        Tier: 🟢 SAFE
        """
        action_clean = action.strip().lower()
        key_map = {
            "play_pause": VK_MEDIA_PLAY_PAUSE,
            "play": VK_MEDIA_PLAY_PAUSE,
            "pause": VK_MEDIA_PLAY_PAUSE,
            "next": VK_MEDIA_NEXT_TRACK,
            "prev": VK_MEDIA_PREV_TRACK,
            "previous": VK_MEDIA_PREV_TRACK,
            "stop": VK_MEDIA_STOP,
            "mute": VK_VOLUME_MUTE,
            "vol_up": VK_VOLUME_UP,
            "vol_down": VK_VOLUME_DOWN,
        }

        vk_code = key_map.get(action_clean)
        if not vk_code:
            return {
                "success": False,
                "error": f"Unknown media action: '{action}'. Available: {list(key_map.keys())}",
            }

        # Send keydown and keyup events via ctypes
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

        return {
            "success": True,
            "action": action_clean,
            "status": f"Triggered media key event: {action_clean.upper()}",
        }
