"""
Ultron Lightweight Agent - Core Module

The LightweightAgent ties together memory, brain, and tools into a single
cohesive agent that can operate in CLI or API mode.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from .brain import Brain
from .memory import Memory
from .tools import CalculatorTool, SystemInfoTool, WebSearchTool
from .tools.base import BaseTool

load_dotenv()
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are Ultron, a lightweight but capable AI assistant.
You have access to memory (conversation history) and a set of tools.
When a user asks you to use a tool, call it by name using the format:
  TOOL:<tool_name> <arg>=<value>

Available tools:
{tool_descriptions}

Always be concise, helpful, and honest. If you are unsure, say so."""


class LightweightAgent:
    """Minimal, self-contained AI agent with memory, an LLM brain, and tools."""

    def __init__(
        self,
        short_term_limit: Optional[int] = None,
        long_term_file: Optional[str] = None,
    ) -> None:
        limit = short_term_limit or int(
            os.getenv("MEMORY_SHORT_TERM_LIMIT", "20")
        )
        ltf = long_term_file or os.getenv(
            "MEMORY_LONG_TERM_FILE", "long_term_memory.json"
        )

        self.memory = Memory(short_term_limit=limit, long_term_file=ltf)
        self.brain = Brain()
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

        logger.info(
            "LightweightAgent ready (backend=%s, tools=%s)",
            self.brain.backend,
            list(self.tools.keys()),
        )

    # ------------------------------------------------------------------
    # Tool management
    # ------------------------------------------------------------------

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance so the agent can invoke it."""
        self.tools[tool.name] = tool
        logger.debug("Tool registered: %s", tool.name)

    def _register_default_tools(self) -> None:
        for tool in [CalculatorTool(), SystemInfoTool(), WebSearchTool()]:
            self.register_tool(tool)

    def _tool_descriptions(self) -> str:
        return "\n".join(
            f"  - {t.name}: {t.description}" for t in self.tools.values()
        )

    # ------------------------------------------------------------------
    # Chat interface
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Process a user message and return the agent's reply.

        The conversation history is stored in short-term memory so the LLM
        receives recent context with every turn.
        """
        user_message = user_message.strip()
        if not user_message:
            return ""

        # Check for slash commands before hitting the LLM
        if user_message.startswith("/"):
            return self._handle_command(user_message)

        # Store the user's turn in short-term memory
        self.memory.add_to_short_term({"role": "user", "content": user_message})

        # Build message list for the LLM (recent history only)
        messages = self.memory.get_short_term()

        system_prompt = _SYSTEM_PROMPT.format(
            tool_descriptions=self._tool_descriptions()
        )

        reply = self.brain.chat(
            messages=messages,
            system_prompt=system_prompt,
        )

        # Check if the LLM wants to invoke a tool
        reply = self._maybe_invoke_tool(reply)

        # Store the assistant reply in short-term memory
        self.memory.add_to_short_term({"role": "assistant", "content": reply})
        return reply

    # ------------------------------------------------------------------
    # Tool invocation
    # ------------------------------------------------------------------

    def _maybe_invoke_tool(self, reply: str) -> str:
        """If the reply starts with TOOL:<name>, execute it and return its output."""
        if not reply.startswith("TOOL:"):
            return reply
        rest = reply[len("TOOL:"):].strip()
        parts = rest.split(None, 1)
        tool_name = parts[0]
        arg_str = parts[1] if len(parts) > 1 else ""

        tool = self.tools.get(tool_name)
        if not tool:
            return f"⚠️  Unknown tool: {tool_name!r}"

        kwargs = self._parse_tool_args(arg_str)
        try:
            result = tool.run(**kwargs)
            return result
        except Exception as exc:
            logger.exception("Tool %r raised an exception", tool_name)
            return f"⚠️  Tool error ({tool_name}): {exc}"

    @staticmethod
    def _parse_tool_args(arg_str: str) -> Dict[str, Any]:
        """Parse ``key=value`` pairs from a tool invocation string."""
        kwargs: Dict[str, Any] = {}
        if not arg_str:
            return kwargs
        # Support quoted values:  key='some value with spaces'
        import re

        for match in re.finditer(r"(\w+)=(?:'([^']*)'|\"([^\"]*)\"|(\\S+))", arg_str):
            key = match.group(1)
            value = match.group(2) or match.group(3) or match.group(4) or ""
            kwargs[key] = value
        # If no key=value pairs found, treat the whole string as positional
        # input by using the generic key "input". Individual tools can handle
        # missing args gracefully via their own defaults.
        if not kwargs and arg_str:
            kwargs["input"] = arg_str
        return kwargs

    # ------------------------------------------------------------------
    # Slash commands
    # ------------------------------------------------------------------

    def _handle_command(self, command: str) -> str:
        """Handle built-in /commands."""
        cmd = command.strip().lower()

        if cmd in ("/help", "/h"):
            return self._help_text()
        if cmd == "/tools":
            return "Available tools:\n" + self._tool_descriptions()
        if cmd in ("/memory", "/mem"):
            return self.memory.get_context_summary()
        if cmd in ("/clear", "/reset"):
            self.memory.clear_short_term()
            return "✅ Short-term memory cleared."
        if cmd == "/status":
            return self._status()
        if cmd.startswith("/remember "):
            fact = command[len("/remember "):].strip()
            key = self.memory.add_to_long_term(fact)
            return f"✅ Remembered (key={key})"
        if cmd.startswith("/recall "):
            query = command[len("/recall "):].strip()
            results = self.memory.search_long_term(query)
            if not results:
                return f"Nothing found in long-term memory for: {query!r}"
            return "\n".join(f"• {v}" for v in results.values())

        return f"⚠️  Unknown command: {command}. Type /help for a list."

    def _help_text(self) -> str:
        return (
            "Ultron Lightweight Agent – available commands:\n"
            "  /help        Show this help message\n"
            "  /tools       List available tools\n"
            "  /memory      Show conversation context summary\n"
            "  /clear       Clear short-term memory\n"
            "  /status      Show agent status\n"
            "  /remember X  Store X in long-term memory\n"
            "  /recall Q    Search long-term memory for Q\n"
        )

    def _status(self) -> str:
        backend_ok = self.brain.is_available()
        return (
            f"Agent status:\n"
            f"  LLM backend:    {self.brain.backend} "
            f"({'✅ reachable' if backend_ok else '❌ not reachable'})\n"
            f"  Tools loaded:   {len(self.tools)} "
            f"({', '.join(self.tools.keys())})\n"
            f"  Short-term mem: {len(self.memory.get_short_term())} messages\n"
            f"  Long-term mem:  {len(self.memory.get_all_long_term())} entries\n"
        )
