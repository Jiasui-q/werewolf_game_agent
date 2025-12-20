# Werewolf Logic Framework (WOLF)

[Sample Assessment on AgentBeats](https://v2.agentbeats.org/view/assessment/abd7e489-910f-42df-86d3-a209bcdaf483)

Werewolf is a classic social deduction game where players are secretly assigned roles and must figure out who among them are the hidden werewolves before they eliminate all the innocent villagers. This is a fantastic testing ground for AI agents since it requires deception, logical reasoning, and social coordination under uncertainty.

## Game Environment

**Roles:**

- 1 Werewolf (trying not to get caught)
- 1 Seer (can investigate players at night)
- 1 Medic (protects people from werewolf attacks)
- Villagers (just trying to survive)

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

Each player is supported by a white agent that receives its secret role as well as the conversations taking place. Multiple white agents can play in the same environment, and they can even be backed by different models. The environment will instantiate extra "NPC" white agents if necessary to make sure the lobby is full.

We use OpenRouter to make it easy to switch between different models and evaluate comparatively.

The interface is purely conversational (no tool calls), and the environment communicates with the agents in natural language.

Our white agent implementation is deliberately simple (just a system prompt and message context), since we are more interested in the behaviors the models "naturally" exhibit.

## Project Structure

```
werewolf_game_agent/
├── agentbeats              # Launch scripts for the different AgentBeats controllers.
│   ├── green
│   │   ├── launch.sh
│   │   └── run.sh
│   ├── white-gemini
│   │   ├── launch.sh
│   │   └── run.sh
│   ├── white-gpt
│   │   ├── launch.sh
│   │   └── run.sh
│   └── white-sonnet
│       ├── launch.sh
│       └── run.sh
├── src
│   ├── green_agent
│   │   ├── agent.py        # Core logic for environment
│   │   └── executor.py     # A2A glue for environment
│   ├── launcher.py         # Launcher functions (powering the CLI)
│   ├── my_util
│   │   └── my_a2a.py       # A2A client for cross-agent communication
│   └── white_agent
│       ├── agent.py        # Core logic for player
│       └── executor.py     # A2A glue for player
└── main.py                 # CLI entrypoint
```

## Installation

```bash
uv sync
```

## Configuration

First, configure `.env` (or set the variable in your shell) so the white agent can reach Gemini:

```bash
OPENROUTER_API_KEY=...
# optionally, set the openrouter model you want to evaluate.
AGENT_MODEL=google/gemini-3-flash-preview
```

## Usage (Local)

To run the environment locally

```bash
# (local) launch the assessment with 5 players
python main.py launch 5
```

## Usage (A2A / AgentBeats)

First, start all the AgentBeats controllers for the various agents.

```bash
# start green agent controller
agentbeats/green/launch.sh

# start controllers for white agents
agentbeats/white-gemini/launch.sh
agentbeats/white-gpt/launch.sh
agentbeats/white-sonnet/launch.sh
```

Then, trigger a run either locally or through the AgentBeats platform.

```bash
python main.py launch-remote <green-url> <white-url-1> <white-url-2> ...
```
