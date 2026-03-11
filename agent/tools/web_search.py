"""
Ultron Lightweight Agent - Web Search Tool

Performs a lightweight web search using the DuckDuckGo Instant Answer API.
No API key required.
"""

import logging
from typing import Any, List

import requests

from .base import BaseTool

logger = logging.getLogger(__name__)

_DDG_URL = "https://api.duckduckgo.com/"


class WebSearchTool(BaseTool):
    """Search the web using the DuckDuckGo Instant Answer API (no API key needed)."""

    name = "web_search"
    description = (
        "Search the web and return an instant answer summary. "
        "Example: web_search query='Python asyncio'"
    )

    def run(self, query: str = "", **kwargs: Any) -> str:  # type: ignore[override]
        """Execute a web search for the given query.

        Args:
            query: The search terms.

        Returns:
            A plain-text summary of the top result, or an error message.
        """
        if not query:
            return "⚠️  No query provided. Usage: web_search query='your question'"
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }
            resp = requests.get(_DDG_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            lines: List[str] = [f"🔍 Search results for: {query!r}", ""]

            abstract = data.get("AbstractText", "").strip()
            if abstract:
                lines.append(abstract)
                source = data.get("AbstractSource", "")
                url = data.get("AbstractURL", "")
                if source:
                    lines.append(f"\nSource: {source}")
                if url:
                    lines.append(f"URL: {url}")
                return "\n".join(lines)

            # Fall back to related topics
            topics: List[str] = []
            for topic in data.get("RelatedTopics", [])[:3]:
                text = topic.get("Text", "").strip()
                if text:
                    topics.append(f"• {text}")
            if topics:
                lines.append("Related results:")
                lines.extend(topics)
                return "\n".join(lines)

            return f"🔍 No instant answer found for: {query!r}"
        except requests.exceptions.ConnectionError:
            logger.warning("Web search failed – no internet connection")
            return "⚠️  Web search unavailable: no internet connection"
        except Exception as exc:
            logger.exception("Web search error for %r", query)
            return f"⚠️  Web search error: {exc}"
