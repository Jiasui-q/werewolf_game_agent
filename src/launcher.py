"""Launcher module - initiates and coordinates the Werewolf evaluation process."""

from __future__ import annotations

import asyncio
import json
import multiprocessing
from typing import Sequence

from green_agent import start_green_agent
from src.my_util import my_a2a
from werewolf_game_agent.green_agent.environment import GameEnvironment
import requests

# Six seats: five local NPCs + one optional remote white agent slot.
DEFAULT_PLAYERS = ["Alice", "Bob", "Charlie", "David", "Eva", "Frank"]


async def _run_remote_flow(
    green_url: str, *white_urls: str
) -> None:
    """Send the werewolf task to the green agent and stream the response."""
    white_url_str = '\n'.join(f"<white_agent_url>\n{url.rstrip('/')}\n</white_agent_url>" for url in white_urls)
    task_text = f"""Your task is to assess the agents located at:
{white_url_str}"""
    print("Task description:")
    print(task_text)
    print("Sending task description to green agent...")
    response = await my_a2a.send_message(green_url, task_text)
    print("Response from green agent:")
    print(response.root)


def launch_evaluation(
    player_names: Sequence[str] | None = None, white_agent_url: str | None = None
) -> None:
    """
    Run a full Werewolf evaluation.

    If `white_agent_url` is provided, spin up the green agent (A2A) and
    instruct it to evaluate the remote white agent. Otherwise, run the
    local simulation using in-process WhiteAgent NPCs for all players.
    """
    players = list(player_names) if player_names else list(DEFAULT_PLAYERS)

    # Local/offline simulation: no remote white agent supplied.
    if not white_agent_url:
        env = GameEnvironment(players)
        env.run_game()
        return

    # Remote evaluation path: start green agent, wait for readiness, send task, then clean up.
    green_address = ("localhost", 9001)
    green_url = f"http://{green_address[0]}:{green_address[1]}"
    print("Launching green agent...")
    p_green = multiprocessing.Process(
        target=start_green_agent, args=("werewolf_green_agent", *green_address)
    )
    p_green.start()
    try:
        ready = asyncio.run(my_a2a.wait_agent_ready(green_url))
        assert ready, "Green agent not ready in time"
        print("Green agent is ready.")

        asyncio.run(_run_remote_flow(green_url, white_agent_url, players))
    finally:
        print("Terminating agents...")
        p_green.terminate()
        p_green.join()
        print("Agents terminated.")

def resolve_agent_from_controller(ctrl_url: str) -> str:
    x = requests.get(f"{ctrl_url}/.well-known/agent-card.json")
    if x.status_code != 404: return ctrl_url # it's already an agent url

    agents = requests.get(f"{ctrl_url}/agents").json()
    agent = list(agents.values())[0]
    return agent['url']

def launch_remote_evaluation(green_url: str, *white_urls: str) -> None:
    """Send a remote evaluation request to an already-running green agent."""
    green_url = resolve_agent_from_controller(green_url)
    white_urls = [resolve_agent_from_controller(url) for url in white_urls]
    asyncio.run(_run_remote_flow(green_url, *white_urls))


__all__ = ["launch_evaluation", "launch_remote_evaluation"]
