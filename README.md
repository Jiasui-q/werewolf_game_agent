# Werewolf Logic Framework (WOLF)

[Sample Assessment on AgentBeats](https://v2.agentbeats.org/view/assessment/abd7e489-910f-42df-86d3-a209bcdaf483)

Werewolf is a classic social deduction game where players are secretly assigned roles and must figure out who among them are the hidden werewolves before they eliminate all the innocent villagers. This is a fantastic testing ground for AI agents since it requires deception, logical reasoning, and social coordination under uncertainty.

## Game Environment

**Roles:**

- 1 Werewolf (trying not to get caught)
- 1 Seer (can investigate players at night)
- 1 Medic (protects people from werewolf attacks)
- 2 Villagers (just trying to survive)

**Game Loop:**

- Day: Everyone argues about who's suspicious, then votes someone out.
- Night: Special roles do their respective actions.
- Repeat until werewolves are eliminated or outnumber everyone else.

## Metrics

### For All Players:

- Team Win - Boolean indicating if their team won the game
- Role - What role they were assigned
- Suspicion Score - How many times they were voted for during the game

### For Non-Werewolf Players Only:

- Voting Accuracy - Percentage of times they voted for the actual werewolf

## Agent Setup

Each player is supported by a white agent that receives the conversation history up to this point. The environment (green agent) controls a number of "NPC" agents, with room for one "player" white agent through the AgentBeats platform.

We use OpenRouter to make it easy to switch between different models based and evaluate comparatively.

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
OPENROUTER_API_KEY=...
```

## Usage (Local)

Note, this doesn't seem to work on Windows due to limitations with the AgentBeats CLI. Definitely use macOS or Linux.

```bash
# launch green agent
agentbeats/green/launch.sh

# launch white agent
agentbeats/white/launch.sh

# (local) launch the assessment
python main.py launch-remote <green_url> <white_url>`
```

## Usage (AgentBeats Platform)

After registering the green and white agents on the AgentBeats platform, simply start a new assessment.
