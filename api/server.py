"""
Ultron Lightweight Agent - REST API Server

Provides two interfaces:
  1. /api/chat              – simple JSON chat endpoint
  2. /v1/chat/completions   – OpenAI-compatible endpoint

Run directly:
    python -m api.server
Or via main.py:
    python main.py --mode api
"""

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.core import LightweightAgent

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message text")


class ChatResponse(BaseModel):
    reply: str


class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str = "ultron-lightweight"
    messages: List[OpenAIMessage]
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False


class OpenAIChoice(BaseModel):
    index: int
    message: OpenAIMessage
    finish_reason: str = "stop"


class OpenAIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenAIChatResponse(BaseModel):
    id: str = "chatcmpl-ultron"
    object: str = "chat.completion"
    model: str = "ultron-lightweight"
    choices: List[OpenAIChoice]
    usage: OpenAIUsage


# -------------------------------------------------------------------------
# App factory
# -------------------------------------------------------------------------


def create_app(agent: Optional[LightweightAgent] = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        agent: An optional pre-initialised LightweightAgent. A new one is
               created automatically when not provided.
    """
    _agent = agent or LightweightAgent()

    app = FastAPI(
        title="Ultron Lightweight Agent API",
        description=(
            "A minimal AI agent API with short-term/long-term memory, "
            "built-in tools, and an OpenAI-compatible chat endpoint."
        ),
        version="1.0.0",
    )

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        """Return the health status of the agent and its LLM backend."""
        return {
            "status": "ok",
            "backend": _agent.brain.backend,
            "backend_available": _agent.brain.is_available(),
            "tools": list(_agent.tools.keys()),
        }

    @app.post("/api/chat", response_model=ChatResponse)
    async def simple_chat(body: ChatRequest) -> ChatResponse:
        """Simple chat endpoint – send a message and get a reply."""
        reply = _agent.chat(body.message)
        return ChatResponse(reply=reply)

    @app.post("/v1/chat/completions", response_model=OpenAIChatResponse)
    async def openai_chat(body: OpenAIChatRequest) -> OpenAIChatResponse:
        """OpenAI-compatible chat completions endpoint.

        Accepts the same request format as the OpenAI Chat API so existing
        clients (LangChain, Continue.dev, etc.) can point at this server.
        """
        if body.stream:
            raise HTTPException(
                status_code=400,
                detail="Streaming is not supported in this lightweight version.",
            )
        if not body.messages:
            raise HTTPException(status_code=400, detail="messages list is empty")

        # Use the last user message as the agent input; earlier messages are
        # already reflected in the agent's in-memory conversation history.
        last = body.messages[-1]
        if last.role != "user":
            raise HTTPException(
                status_code=400,
                detail="The last message must have role='user'.",
            )

        reply = _agent.chat(last.content)

        return OpenAIChatResponse(
            model=body.model,
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content=reply),
                )
            ],
            usage=OpenAIUsage(),
        )

    return app


# -------------------------------------------------------------------------
# Standalone entry point
# -------------------------------------------------------------------------


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    agent: Optional[LightweightAgent] = None,
) -> None:
    """Start the Uvicorn server."""
    import uvicorn

    app = create_app(agent=agent)
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Ultron API server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server(
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
    )
