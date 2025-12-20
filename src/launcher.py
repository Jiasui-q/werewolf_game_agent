"""Launcher module - initiates and coordinates the Werewolf evaluation process."""

from __future__ import annotations

import asyncio

from green_agent.agent import AsyncGameEnvironment
from src.my_util import my_a2a
import requests


def launch_evaluation(
    player_count: int | None = None
) -> None:
    """
    Run a full Werewolf evaluation.
    """

    # Local/offline simulation: no remote white agent supplied.
    env = AsyncGameEnvironment([], player_count)
    asyncio.run(env.run_game())

def resolve_agent_from_controller(ctrl_url: str) -> str:
    x = requests.get(f"{ctrl_url}/.well-known/agent-card.json")
    if x.status_code != 404: return ctrl_url # it's already an agent url

    agents = requests.get(f"{ctrl_url}/agents").json()
    agent = list(agents.values())[0]
    return agent['url']



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

def launch_remote_evaluation(green_url: str, *white_urls: str) -> None:
    """Send a remote evaluation request to an already-running green agent."""
    green_url = resolve_agent_from_controller(green_url)
    white_urls = [resolve_agent_from_controller(url) for url in white_urls]
    asyncio.run(_run_remote_flow(green_url, *white_urls))


__all__ = ["launch_evaluation", "launch_remote_evaluation"]
