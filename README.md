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
pip install earthshaker
```

## Configuration

First, configure `.env` (or set the variable in your shell) so the white agent can reach Gemini:

```
GEMINI_API_KEY=...
```

## Usage

1. Make the provided `run.sh` executable and use it to start your Werewolf agent for the controller to manage:

   ```bash
   chmod +x run.sh
   ./run.sh
   ```

2. Launch the AgentBeats controller so the platform can check/reset the agent and proxy traffic:

   ```bash
   agentbeats run_ctrl
   ```

3. Register the controller URL with AgentBeats and point the agent card URL to `https://<your-host>/.well-known/agent-card.json`. Keep `/status` available so AgentBeats can verify the controller is healthy before fetching the card content.

The FastAPI controller continues to expose `/agent_info`, `/task`, `/reset`, `/logs`, `/status`, and `/agent-card` so any MCP-compatible tooling can interact with your agent.
