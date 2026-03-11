"""Tests for api/server.py"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from api.server import create_app
from agent.core import LightweightAgent


@pytest.fixture
def agent(tmp_path):
    return LightweightAgent(
        short_term_limit=10,
        long_term_file=str(tmp_path / "lt.json"),
    )


@pytest.fixture
def client(agent):
    app = create_app(agent=agent)
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "backend" in data
        assert "tools" in data

    def test_health_lists_tools(self, client):
        data = client.get("/health").json()
        assert "calculator" in data["tools"]
        assert "system_info" in data["tools"]


class TestSimpleChatEndpoint:
    def test_slash_command(self, client):
        resp = client.post("/api/chat", json={"message": "/help"})
        assert resp.status_code == 200
        assert "/tools" in resp.json()["reply"]

    def test_llm_reply(self, client, agent):
        with patch.object(agent.brain, "chat", return_value="I am Ultron."):
            resp = client.post("/api/chat", json={"message": "Who are you?"})
        assert resp.status_code == 200
        assert "Ultron" in resp.json()["reply"]

    def test_missing_message_field(self, client):
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 422  # validation error


class TestOpenAICompatibleEndpoint:
    def test_basic_completion(self, client, agent):
        with patch.object(agent.brain, "chat", return_value="Hello!"):
            resp = client.post(
                "/v1/chat/completions",
                json={
                    "model": "ultron-lightweight",
                    "messages": [{"role": "user", "content": "Hi"}],
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert data["choices"][0]["message"]["content"] == "Hello!"

    def test_empty_messages_rejected(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={"model": "ultron-lightweight", "messages": []},
        )
        assert resp.status_code == 400

    def test_last_message_must_be_user(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "ultron-lightweight",
                "messages": [{"role": "assistant", "content": "..."}],
            },
        )
        assert resp.status_code == 400

    def test_stream_not_supported(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "ultron-lightweight",
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": True,
            },
        )
        assert resp.status_code == 400
