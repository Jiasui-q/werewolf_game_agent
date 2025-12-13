"""Utility launcher that orchestrates the Werewolf evaluation flow."""

from __future__ import annotations

from typing import Sequence

from werewolf_game_agent.green_agent.environment import GameEnvironment

DEFAULT_PLAYERS = ["Alice", "Bob", "Charlie", "David", "Eva"]


def launch_evaluation(player_names: Sequence[str] | None = None) -> None:
    """Create the evaluation environment and run a single match."""
    players = list(player_names) if player_names else list(DEFAULT_PLAYERS)
    env = GameEnvironment(players)
    env.run_game()


def launch_remote_evaluation(green_url: str, white_url: str) -> None:
    """Remote evaluations are not implemented for this demo."""
    raise NotImplementedError("Remote evaluation is not supported for this project.")
