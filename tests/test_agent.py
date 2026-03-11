"""Tests for agent/core.py (LightweightAgent)"""

import pytest
from unittest.mock import MagicMock, patch

from agent.core import LightweightAgent
from agent.tools.base import BaseTool


@pytest.fixture
def agent(tmp_path):
    """Create a LightweightAgent backed by a temporary memory file."""
    return LightweightAgent(
        short_term_limit=10,
        long_term_file=str(tmp_path / "lt.json"),
    )


class TestAgentInit:
    def test_tools_registered(self, agent):
        assert "calculator" in agent.tools
        assert "system_info" in agent.tools
        assert "web_search" in agent.tools

    def test_memory_initialised(self, agent):
        assert agent.memory is not None

    def test_brain_initialised(self, agent):
        assert agent.brain is not None


class TestSlashCommands:
    def test_help_command(self, agent):
        reply = agent.chat("/help")
        assert "/tools" in reply
        assert "/memory" in reply

    def test_tools_command(self, agent):
        reply = agent.chat("/tools")
        assert "calculator" in reply
        assert "system_info" in reply

    def test_memory_command_empty(self, agent):
        reply = agent.chat("/memory")
        assert "No prior context" in reply or "memory" in reply.lower()

    def test_clear_command(self, agent):
        agent.memory.add_to_short_term({"role": "user", "content": "hi"})
        reply = agent.chat("/clear")
        assert "cleared" in reply.lower()
        assert agent.memory.get_short_term() == []

    def test_status_command(self, agent):
        reply = agent.chat("/status")
        assert "backend" in reply.lower()

    def test_remember_and_recall(self, agent):
        agent.chat("/remember Python is my favourite language")
        reply = agent.chat("/recall Python")
        assert "Python" in reply

    def test_unknown_command(self, agent):
        reply = agent.chat("/nonexistent")
        assert "Unknown command" in reply or "⚠️" in reply


class TestToolInvocation:
    def test_calculator_via_tool_prefix(self, agent):
        """Agent core should execute TOOL:calculator if LLM returns that prefix."""
        with patch.object(agent.brain, "chat", return_value="TOOL:calculator expression='3 + 4'"):
            reply = agent.chat("What is 3 + 4?")
        assert reply == "7"

    def test_unknown_tool_returns_warning(self, agent):
        with patch.object(agent.brain, "chat", return_value="TOOL:nonexistent_tool"):
            reply = agent.chat("do something")
        assert "Unknown tool" in reply

    def test_normal_llm_reply_passes_through(self, agent):
        with patch.object(agent.brain, "chat", return_value="Hello, I am Ultron."):
            reply = agent.chat("Introduce yourself")
        assert reply == "Hello, I am Ultron."


class TestMemoryIntegration:
    def test_conversation_stored_in_short_term(self, agent):
        with patch.object(agent.brain, "chat", return_value="Hi there!"):
            agent.chat("Hello")
        history = agent.memory.get_short_term()
        assert any(m["role"] == "user" for m in history)
        assert any(m["role"] == "assistant" for m in history)

    def test_empty_message_returns_empty(self, agent):
        reply = agent.chat("   ")
        assert reply == ""


class TestCustomTool:
    def test_register_custom_tool(self, agent):
        class EchoTool(BaseTool):
            name = "echo"
            description = "Echoes the input"

            def run(self, text="", **kwargs):
                return f"Echo: {text}"

        agent.register_tool(EchoTool())
        assert "echo" in agent.tools

    def test_invoke_custom_tool(self, agent):
        class EchoTool(BaseTool):
            name = "echo"
            description = "Echoes the input"

            def run(self, text="", **kwargs):
                return f"Echo: {text}"

        agent.register_tool(EchoTool())
        with patch.object(agent.brain, "chat", return_value="TOOL:echo text='hello world'"):
            reply = agent.chat("echo this")
        assert reply == "Echo: hello world"
