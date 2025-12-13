"""Wrapper for running the Werewolf assessment from the green-agent perspective."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Sequence

import tomllib

from werewolf_game_agent.green_agent.environment import GameEnvironment

DEFAULT_PLAYERS = ["Alice", "Bob", "Charlie", "David", "Eva"]


def load_agent_card_toml(agent_name: str):
    """Load the agent descriptor that AgentBeats expects."""
    card_path = Path(__file__).with_name(f"{agent_name}.toml")
    with card_path.open("rb") as handler:
        return tomllib.load(handler)


def start_green_agent(
    agent_name: str = "werewolf_green_agent",
    player_names: Sequence[str] | None = None,
    host: str = "localhost",
    port: int = 9001,
) -> None:
    """Kick off the werewolf game loop from the green-agent (assessment-host) side."""
    players = list(player_names) if player_names else list(DEFAULT_PLAYERS)
    agent_card = load_agent_card_toml(agent_name)
    agent_card["url"] = os.getenv("AGENT_URL", f"http://{host}:{port}")

    print(f"Launching green agent with card:\n{json.dumps(agent_card, indent=2)}")
    env = GameEnvironment(players)
    env.run_game()
