"""
Web Navigator for F.L.A.R.E Hands.
Provides smart URL opening and targeted web searching across major engines (Google, Brave, GitHub, Reddit, Wikipedia).
"""

import os
import urllib.parse
from typing import Any, Dict, Optional


class WebNavigator:
    """Handles browser navigation and multi-engine web queries."""

    ENGINES = {
        "google": "https://www.google.com/search?q=",
        "brave": "https://search.brave.com/search?q=",
        "duckduckgo": "https://duckduckgo.com/?q=",
        "bing": "https://www.bing.com/search?q=",
        "github": "https://github.com/search?q=",
        "reddit": "https://www.reddit.com/search/?q=",
        "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=",
        "youtube": "https://www.youtube.com/results?search_query=",
    }

    @classmethod
    def search_web_and_open(
        cls,
        query: str,
        engine: str = "brave",
        browser: str = "brave",
    ) -> Dict[str, Any]:
        """
        Search the web on a specified engine and launch in the selected browser.
        Tier: 🟡 CONFIRM
        """
        clean_query = query.strip()
        encoded = urllib.parse.quote_plus(clean_query)
        eng_key = engine.strip().lower()
        base_url = cls.ENGINES.get(eng_key, cls.ENGINES["brave"])

        target_url = f"{base_url}{encoded}"

        from hands.system_control.app_manager import AppManager
        res = AppManager.open_app(browser, arguments=target_url)

        if res.get("launched"):
            return {
                "success": True,
                "query": clean_query,
                "engine": eng_key,
                "browser": browser,
                "url": target_url,
                "status": f"Searched '{clean_query}' on {eng_key.title()} via {browser.title()}.",
            }
        else:
            try:
                os.startfile(target_url)
                return {
                    "success": True,
                    "query": clean_query,
                    "engine": eng_key,
                    "browser": "default",
                    "url": target_url,
                    "status": f"Searched '{clean_query}' on {eng_key.title()} via default browser.",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to open search URL: {str(e)}",
                }

    @staticmethod
    def open_url(url: str, browser: str = "brave") -> Dict[str, Any]:
        """
        Open any URL directly in the specified browser.
        Tier: 🟡 CONFIRM
        """
        target = url.strip()
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        from hands.system_control.app_manager import AppManager
        res = AppManager.open_app(browser, arguments=target)

        if res.get("launched"):
            return {
                "success": True,
                "url": target,
                "browser": browser,
                "status": f"Opened '{target}' in {browser.title()}.",
            }
        else:
            try:
                os.startfile(target)
                return {
                    "success": True,
                    "url": target,
                    "browser": "default",
                    "status": f"Opened '{target}' in default browser.",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to open URL: {str(e)}",
                }
