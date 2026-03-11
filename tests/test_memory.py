"""Tests for agent/memory.py"""

import os
import tempfile

import pytest

from agent.memory import Memory


@pytest.fixture
def mem(tmp_path):
    """Return a Memory instance backed by a temporary file."""
    return Memory(short_term_limit=5, long_term_file=str(tmp_path / "lt.json"))


class TestShortTermMemory:
    def test_add_and_retrieve(self, mem):
        mem.add_to_short_term({"role": "user", "content": "hello"})
        assert mem.get_short_term() == [{"role": "user", "content": "hello"}]

    def test_limit_enforced(self, mem):
        for i in range(10):
            mem.add_to_short_term({"role": "user", "content": str(i)})
        items = mem.get_short_term()
        assert len(items) == 5
        assert items[-1]["content"] == "9"

    def test_clear(self, mem):
        mem.add_to_short_term("item")
        mem.clear_short_term()
        assert mem.get_short_term() == []


class TestLongTermMemory:
    def test_add_and_get(self, mem):
        key = mem.add_to_long_term("remember this")
        assert mem.get_long_term(key) == "remember this"

    def test_missing_key_returns_none(self, mem):
        assert mem.get_long_term("nonexistent") is None

    def test_search(self, mem):
        mem.add_to_long_term("Python is great", key="py")
        mem.add_to_long_term("Rust is fast", key="rs")
        results = mem.search_long_term("python")
        assert "py" in results
        assert "rs" not in results

    def test_delete(self, mem):
        key = mem.add_to_long_term("to be deleted")
        assert mem.delete_long_term(key) is True
        assert mem.get_long_term(key) is None

    def test_delete_missing_returns_false(self, mem):
        assert mem.delete_long_term("ghost") is False

    def test_persistence(self, tmp_path):
        ltf = str(tmp_path / "lt.json")
        m1 = Memory(long_term_file=ltf)
        m1.add_to_long_term("persisted fact", key="fact1")

        # A fresh Memory instance loading the same file
        m2 = Memory(long_term_file=ltf)
        assert m2.get_long_term("fact1") == "persisted fact"

    def test_clear_long_term(self, mem):
        mem.add_to_long_term("x", key="k1")
        mem.clear_long_term()
        assert mem.get_all_long_term() == {}


class TestContextSummary:
    def test_empty_summary(self, mem):
        summary = mem.get_context_summary()
        assert "No prior context" in summary

    def test_summary_with_messages(self, mem):
        mem.add_to_short_term({"role": "user", "content": "hi"})
        mem.add_to_short_term({"role": "assistant", "content": "hello"})
        summary = mem.get_context_summary()
        assert "user" in summary
        assert "assistant" in summary
