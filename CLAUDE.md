# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Minimal LLM-driven code agent using Python + OpenAI-compatible API. Single-file ReAct loop that reads/writes files and executes commands via tool calling.

## Commands

```bash
# Run the agent
uv run agent.py

# Install/sync dependencies
uv sync
```

## Architecture

Everything lives in `agent.py` (~210 lines):

1. **Config** — Reads `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL_NAME` from `.env` via python-dotenv
2. **Tools** — 4 tools (`read_file`, `write_file`, `run_command`, `list_files`) defined as OpenAI function-calling JSON schemas, with matching Python implementations
3. **Path resolution** — `_resolve()` maps relative paths to `./action/` working directory; all file and command operations are sandboxed there
4. **Agent loop** — `chat()` runs a ReAct loop: send messages to LLM → if tool_calls, execute and append results → repeat until LLM returns text
5. **CLI** — `main()` provides interactive multi-turn conversation, maintains message history

## Key Design Decisions

- All agent file operations target `./action/` directory, not the project root
- Uses OpenAI-compatible API (works with any provider that supports the same interface)
- Commands have a 30-second timeout
- `list_files` skips hidden dirs, `__pycache__`, and `node_modules`
