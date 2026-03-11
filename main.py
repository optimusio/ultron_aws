#!/usr/bin/env python3
"""
Ultron Lightweight Agent - Main entry point

Usage:
    python main.py               # interactive CLI (default)
    python main.py --mode cli    # interactive CLI
    python main.py --mode api    # REST API server (port 8000)
    python main.py --mode api --port 9000
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(name)-24s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )


def _run_cli(agent) -> None:
    """Interactive CLI loop."""
    print("╔══════════════════════════════════════════════╗")
    print("║   Ultron Lightweight Agent  –  CLI Mode      ║")
    print("║   Type /help for commands, Ctrl-C to exit    ║")
    print("╚══════════════════════════════════════════════╝\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not user_input:
            continue
        reply = agent.chat(user_input)
        print(f"Ultron: {reply}\n")


def _run_api(agent, host: str, port: int) -> None:
    """Start the FastAPI server."""
    from api.server import run_server

    run_server(host=host, port=port, agent=agent)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ultron Lightweight Agent",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["cli", "api"],
        default="cli",
        help="Run as interactive CLI or REST API server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Port for the API server (--mode api only)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind the API server to",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    _setup_logging(args.log_level)

    try:
        from agent.core import LightweightAgent

        agent = LightweightAgent()
    except Exception as exc:
        print(f"Failed to initialise agent: {exc}", file=sys.stderr)
        return 1

    if args.mode == "api":
        _run_api(agent, host=args.host, port=args.port)
    else:
        _run_cli(agent)

    return 0


if __name__ == "__main__":
    sys.exit(main())
