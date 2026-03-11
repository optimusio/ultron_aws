"""
Ultron Lightweight Agent - Memory Module

Provides a two-tier memory system:
  - Short-term: a fixed-size in-memory deque (conversation context)
  - Long-term: persistent JSON file storage (facts and important information)
"""

import json
import logging
import os
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Memory:
    """Two-tier memory system: in-memory short-term + JSON-backed long-term."""

    def __init__(
        self,
        short_term_limit: int = 20,
        long_term_file: str = "long_term_memory.json",
    ) -> None:
        self.short_term_memory: deque = deque(maxlen=short_term_limit)
        self.long_term_file = long_term_file
        self.long_term_memory: Dict[str, Any] = self._load_long_term()
        logger.info(
            "Memory initialized (short_term_limit=%d, long_term_entries=%d)",
            short_term_limit,
            len(self.long_term_memory),
        )

    # ------------------------------------------------------------------
    # Short-term memory
    # ------------------------------------------------------------------

    def add_to_short_term(self, item: Any) -> None:
        """Append an item to short-term memory."""
        self.short_term_memory.append(item)
        logger.debug("Short-term memory updated (%d items)", len(self.short_term_memory))

    def get_short_term(self) -> List[Any]:
        """Return all current short-term memory items as a list."""
        return list(self.short_term_memory)

    def clear_short_term(self) -> None:
        """Clear all short-term memory."""
        self.short_term_memory.clear()
        logger.debug("Short-term memory cleared")

    # ------------------------------------------------------------------
    # Long-term memory
    # ------------------------------------------------------------------

    def add_to_long_term(self, item: Any, key: Optional[str] = None) -> str:
        """Store an item in long-term memory and persist to disk.

        Args:
            item: The data to store.
            key: Optional explicit key. A UUID is generated when omitted.

        Returns:
            The key under which the item was stored.
        """
        if key is None:
            key = str(uuid.uuid4())
        self.long_term_memory[key] = {
            "value": item,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._save_long_term()
        logger.debug("Long-term memory updated (key=%s)", key)
        return key

    def get_long_term(self, key: str) -> Optional[Any]:
        """Retrieve a long-term memory entry by key, or None if absent."""
        entry = self.long_term_memory.get(key)
        return entry["value"] if entry else None

    def search_long_term(self, query: str) -> Dict[str, Any]:
        """Simple substring search across long-term memory values.

        Returns a dict of matching {key: value} pairs.
        """
        query_lower = query.lower()
        results: Dict[str, Any] = {}
        for key, entry in self.long_term_memory.items():
            value_str = str(entry.get("value", "")).lower()
            if query_lower in value_str:
                results[key] = entry["value"]
        return results

    def get_all_long_term(self) -> Dict[str, Any]:
        """Return all long-term memory entries as {key: value} dict."""
        return {k: v["value"] for k, v in self.long_term_memory.items()}

    def delete_long_term(self, key: str) -> bool:
        """Delete a long-term memory entry. Returns True if it existed."""
        if key in self.long_term_memory:
            del self.long_term_memory[key]
            self._save_long_term()
            logger.debug("Long-term memory entry deleted (key=%s)", key)
            return True
        return False

    def clear_long_term(self) -> None:
        """Delete all long-term memory and remove the backing file."""
        self.long_term_memory.clear()
        try:
            Path(self.long_term_file).unlink(missing_ok=True)
        except Exception:
            logger.exception("Failed to delete long-term memory file")
        logger.debug("Long-term memory cleared")

    # ------------------------------------------------------------------
    # Summary helper (used by the agent to build LLM context)
    # ------------------------------------------------------------------

    def get_context_summary(self, max_short_term: int = 10) -> str:
        """Return a concise text summary of recent memory for LLM context."""
        lines: List[str] = []
        recent = list(self.short_term_memory)[-max_short_term:]
        if recent:
            lines.append("Recent conversation:")
            for item in recent:
                role = item.get("role", "unknown")
                content = item.get("content", "")
                lines.append(f"  [{role}] {content}")
        lt_count = len(self.long_term_memory)
        if lt_count:
            lines.append(f"Long-term memory: {lt_count} stored entries.")
        return "\n".join(lines) if lines else "No prior context."

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_long_term(self) -> Dict[str, Any]:
        """Load long-term memory from disk; return empty dict on any error."""
        path = Path(self.long_term_file)
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                logger.exception("Failed to load long-term memory from %s", path)
        return {}

    def _save_long_term(self) -> None:
        """Persist long-term memory to disk."""
        try:
            with open(self.long_term_file, "w", encoding="utf-8") as fh:
                json.dump(self.long_term_memory, fh, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("Failed to save long-term memory to %s", self.long_term_file)
