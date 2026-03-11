"""
Ultron Lightweight Agent - Base Tool

All tools inherit from BaseTool and expose a uniform interface so the agent
core can discover and invoke them dynamically.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Abstract base class for all Ultron tools."""

    #: Machine-readable name used to invoke the tool.
    name: str = ""
    #: Human-readable description shown in ``/tools`` and LLM context.
    description: str = ""

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        """Execute the tool with the provided keyword arguments.

        Returns:
            A plain-text result string.
        """

    def get_schema(self) -> Dict[str, Any]:
        """Return a minimal JSON-schema-style description for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
        }

    def __repr__(self) -> str:
        return f"<Tool name={self.name!r}>"
