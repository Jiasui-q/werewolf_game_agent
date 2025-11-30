# Werewolf Logic Framework (WOLF)

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

Each player is supported by a white agent that receives the conversation history up to this point. They are then asked to make a statement and vote for the most suspicious player (using a tool call).

At the moment, we are using `llama-3.1-8b-instant` hosted on Groq, but we plan to expand our list of models and have them compete against each other to do a comparative analysis.

## Setup

Python 3.11.9

```bash
# create a virtual environment
python -m venv .venv
# activate the environment
. .venv/bin/activate
# install the required packages
pip install -r requirements.txt
# run the project
python main.py

## AgentBeats v2 Compatibility

This repo now exposes an AgentBeats-compatible controller.

**Endpoints:** `/agent_info`, `/task`, `/reset`, `/logs` (FastAPI on port 8010).

**Run locally (mimics `agentbeats run_ctrl`):**
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python agentbeats.py run_ctrl
```
You should see `Starting controller on http://0.0.0.0:8010`.

**Env vars before running (per platform guidance):**
- `HTTPS_ENABLED=true` to announce an https URL.
- `CLOUDRUN_HOST=<your cloudflare domain>` to print the external URL (e.g., `youragent.example.com`).
- `ROLE=<optional role label>` if you host multiple agents from one repo.

**Cloudflare Tunnel (summary):**
1) Create a tunnel in Zero Trust → Tunnels and run `cloudflared tunnel run <ID>`.
2) Add a route: Hostname = youragent.yourdomain.com, Service = HTTP → `http://localhost:8010`.
3) Your controller becomes reachable at `https://youragent.yourdomain.com` for registration.
```
