"""
Ultron Lightweight Agent - Brain Module

Handles communication with the configured LLM backend:
  - Ollama  (default) – local models via HTTP API
  - OpenAI / OpenAI-compatible APIs – cloud models

Backend is selected via the ULTRON_LLM_BACKEND environment variable.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class Brain:
    """LLM integration layer supporting Ollama and OpenAI-compatible backends."""

    def __init__(self) -> None:
        self.backend: str = os.getenv("ULTRON_LLM_BACKEND", "ollama").lower()

        # --- Ollama settings ---
        self.ollama_base_url: str = os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        ).rstrip("/")
        self.ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

        # --- OpenAI settings ---
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_base_url: str = os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com"
        ).rstrip("/")

        logger.info(
            "Brain initialized (backend=%s, model=%s)",
            self.backend,
            self.ollama_model if self.backend == "ollama" else self.openai_model,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Send a list of chat messages to the LLM and return the reply.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            system_prompt: Optional system-level instruction prepended to the
                conversation.
            temperature: Sampling temperature (0.0–1.0).
            max_tokens: Maximum tokens in the reply.

        Returns:
            The assistant's reply as a plain string.
        """
        if system_prompt:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            full_messages = messages

        if self.backend == "ollama":
            return self._ollama_chat(full_messages, temperature, max_tokens)
        return self._openai_chat(full_messages, temperature, max_tokens)

    def is_available(self) -> bool:
        """Return True when the configured backend appears reachable."""
        try:
            if self.backend == "ollama":
                resp = requests.get(f"{self.ollama_base_url}/api/tags", timeout=3)
                return resp.status_code == 200
            # OpenAI – just check an API key is set
            return bool(self.openai_api_key)
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Return available model names from the configured backend."""
        try:
            if self.backend == "ollama":
                resp = requests.get(
                    f"{self.ollama_base_url}/api/tags", timeout=5
                )
                resp.raise_for_status()
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            logger.warning("Could not list models from backend", exc_info=True)
        return []

    # ------------------------------------------------------------------
    # Backend implementations
    # ------------------------------------------------------------------

    def _ollama_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the Ollama /api/chat endpoint."""
        url = f"{self.ollama_base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot reach Ollama at %s", self.ollama_base_url)
            return (
                "⚠️  Ollama is not reachable. "
                "Please start it with `ollama serve` and ensure the model "
                f"'{self.ollama_model}' is pulled."
            )
        except Exception as exc:
            logger.exception("Ollama chat error")
            return f"⚠️  LLM error: {exc}"

    def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call an OpenAI-compatible /v1/chat/completions endpoint."""
        if not self.openai_api_key:
            return (
                "⚠️  OPENAI_API_KEY is not set. "
                "Set it in your environment or .env file."
            )
        url = f"{self.openai_base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.openai_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
        except Exception as exc:
            logger.exception("OpenAI chat error")
            return f"⚠️  LLM error: {exc}"
