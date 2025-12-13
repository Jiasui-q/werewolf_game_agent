"""CLI entry point for the Werewolf Game Agent (inspired by agentify-example-tau-bench)."""

from __future__ import annotations

import asyncio
from typing import List, Optional

import typer
from pydantic import BaseSettings

from launcher import launch_evaluation, launch_remote_evaluation
from white_agent import start_white_agent
from green_agent import start_green_agent


class WerewolfSettings(BaseSettings):
    role: str = "unspecified"
    host: str = "127.0.0.1"
    agent_port: int = 9000


app = typer.Typer(help="Agentified Werewolf Game Agent (AgentBeats compatible).")


@app.command()
def green() -> None:
    """Start the green agent (assessment manager)."""
    start_green_agent()


@app.command()
def white() -> None:
    """Start the white agent (target under evaluation)."""
    start_white_agent()


@app.command()
def run() -> None:
    """Start whichever agent corresponds to ROLE."""
    settings = WerewolfSettings()
    if settings.role == "green":
        start_green_agent(host=settings.host, port=settings.agent_port)
    elif settings.role == "white":
        start_white_agent(host=settings.host, port=settings.agent_port)
    else:
        raise typer.BadParameter(f"Unknown role: {settings.role}")


@app.command()
def launch(players: Optional[List[str]] = typer.Option(None, "--players", "-p", help="Explicit player roster to use.")) -> None:
    """Launch a complete Werewolf evaluation."""
    launch_evaluation(players)


@app.command()
def launch_remote(green_url: str, white_url: str) -> None:
    """Attempt a remote evaluation (not yet supported)."""
    asyncio.run(launch_remote_evaluation(green_url, white_url))


if __name__ == "__main__":
    app()
