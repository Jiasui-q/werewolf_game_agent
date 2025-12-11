# Werewolf Game Agent (AgentBeats)

Example agent for the AgentBeats platform that hosts the classic Werewolf social deduction game and exposes the A2A/MCP-compatible controller.

## Project Structure

```
src/
└── werewolf_game_agent/
    ├── agentbeats.py      # AgentBeats-compatible controller shim
    ├── controller.py      # FastAPI controller for `/task`, `/agent_info`, etc.
    ├── agent_logic.py     # Shared exports for white-agent logic
    ├── launcher.py        # Tau-Bench/Agentify-style evaluation runner
    ├── green_agent/       # Assessment manager environment
    └── white_agent/       # Gemini-powered target agent
main.py                    # CLI entry point (uv run python main.py launch)
pyproject.toml             # uv sync manifest
README.md                  # This document
.python-version            # Recommended Python version
.gitignore                 # Workspace hygiene
```

## Installation

```bash
uv sync
```

## Configuration

First, configure `.env` (or set the variable in your shell) so the white agent can reach Gemini:

```
GEMINI_API_KEY=...
```

## Usage

```bash
# Launch the whole evaluation
uv run python main.py launch
```

This command runs the Werewolf `GameEnvironment` with the green/white agents and prints the post-game metrics.

AgentBeats compatibility remains available:

```bash
agentbeats run_ctrl
```

The FastAPI controller exposes `/agent_info`, `/task`, `/reset`, and `/logs` on port 8010 for registration with MCP or other tooling.
