# Ultron Lightweight Agent

A minimal, self-contained Python AI agent inspired by [Ultron Agent 3.0](https://github.com/optimusio/ultron_agent). It strips the full platform down to its essential core — an LLM brain, a two-tier memory system, a small set of built-in tools, and a REST API — so it runs on any machine with Python 3.11+ and no GPU required.

## Architecture

```
ultron_aws/
├── agent/
│   ├── core.py        ← LightweightAgent (ties everything together)
│   ├── memory.py      ← Short-term (deque) + long-term (JSON) memory
│   ├── brain.py       ← LLM integration: Ollama or OpenAI-compatible
│   └── tools/
│       ├── base.py        ← BaseTool abstract class
│       ├── calculator.py  ← Safe arithmetic evaluator (no eval())
│       ├── system_info.py ← CPU / memory / disk metrics (psutil)
│       └── web_search.py  ← DuckDuckGo Instant Answer search
├── api/
│   └── server.py      ← FastAPI: /health, /api/chat, /v1/chat/completions
├── tests/             ← pytest test suite
├── main.py            ← CLI and API entry point
└── requirements.txt   ← Minimal dependencies (~10 packages)
```

## What's included vs the full Ultron Agent

| Feature | Full Ultron Agent | Lightweight |
|---|---|---|
| LLM backend (Ollama / OpenAI) | ✅ | ✅ |
| Short-term + long-term memory | ✅ | ✅ |
| REST API (OpenAI-compatible) | ✅ | ✅ |
| Built-in tools | 15+ | 3 (calculator, system_info, web_search) |
| GUI / voice / vision | ✅ | ❌ |
| PyTorch / Transformers | ✅ | ❌ |
| LangChain / LangFlow | ✅ | ❌ |
| AWS Bedrock / Lambda | ✅ | ❌ |
| Dependencies | 50+ packages | ~10 packages |
| Min RAM | ~4 GB | < 512 MB |

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set ULTRON_LLM_BACKEND, model names, API keys, etc.
```

### 3. Start Ollama (recommended backend)

```bash
# Install: https://ollama.ai/download
ollama serve
ollama pull llama3.2:latest   # or any other model
```

### 4. Run

**Interactive CLI:**
```bash
python main.py
# or explicitly:
python main.py --mode cli
```

**REST API server (port 8000):**
```bash
python main.py --mode api
```

## CLI Usage

```
You: /help          → list commands
You: /tools         → list available tools
You: /status        → show agent + LLM status
You: /memory        → show conversation context
You: /clear         → clear short-term memory
You: /remember X    → store X in long-term memory
You: /recall Q      → search long-term memory for Q
You: What is 12 * 7?   → regular chat (uses LLM)
```

## API Endpoints

Once the server is running at `http://localhost:8000`:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/chat` | POST | Simple chat: `{"message": "..."}` |
| `/v1/chat/completions` | POST | OpenAI-compatible endpoint |

### Example – simple chat

```bash
curl -s http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/status"}' | python -m json.tool
```

### Example – OpenAI-compatible

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ultron-lightweight",
    "messages": [{"role": "user", "content": "What is 2 ** 10?"}]
  }' | python -m json.tool
```

Because the endpoint is OpenAI-compatible, you can point tools like
**Continue.dev** or **LangChain** at `http://localhost:8000` directly.

## Configuration Reference

All settings can be placed in a `.env` file (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `ULTRON_LLM_BACKEND` | `ollama` | `ollama` or `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:latest` | Model to use with Ollama |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `OPENAI_BASE_URL` | `https://api.openai.com` | Override for LM Studio / Groq / etc. |
| `MEMORY_SHORT_TERM_LIMIT` | `20` | Max conversation turns in short-term memory |
| `MEMORY_LONG_TERM_FILE` | `long_term_memory.json` | Path to long-term memory file |
| `API_HOST` | `0.0.0.0` | API server bind host |
| `API_PORT` | `8000` | API server port |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Adding Custom Tools

Subclass `BaseTool` and register it with the agent:

```python
from agent.tools.base import BaseTool
from agent.core import LightweightAgent

class GreetTool(BaseTool):
    name = "greet"
    description = "Greet someone by name. Usage: greet name='Alice'"

    def run(self, name: str = "world", **kwargs) -> str:
        return f"Hello, {name}!"

agent = LightweightAgent()
agent.register_tool(GreetTool())
print(agent.chat("/tools"))   # 'greet' now appears in the list
```

## Running Tests

```bash
pytest tests/ -v
```

## Docker

```bash
# Build
docker build -t ultron-lightweight -f deployment/Dockerfile .

# Run API server
docker run -p 8000:8000 \
  -e ULTRON_LLM_BACKEND=ollama \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ultron-lightweight
```

See `deployment/README.md` for full Docker instructions.

## Contributing

Pull requests are welcome! If you find issues or have suggestions, open an issue or submit a PR.
