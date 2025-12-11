"""Launcher script that coordinates a full Werewolf evaluation."""

from __future__ import annotations

from typing import Sequence

from werewolf_game_agent.green_agent import GameEnvironment

DEFAULT_PLAYERS = ["Alice", "Bob", "Charlie", "David", "Eva"]


def launch_evaluation(player_names: Sequence[str] | None = None) -> None:
    """Create the environment and run through a single evaluation."""
    players = list(player_names) if player_names else DEFAULT_PLAYERS.copy()
    env = GameEnvironment(players)
    env.run_game()
