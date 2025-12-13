"""Minimal entry point for the Werewolf white agent (target player)."""

from __future__ import annotations

def start_white_agent(host: str = "localhost", port: int = 9002) -> None:
    """Explain that the controller proxies to this agent."""
    print("The Werewolf white agent exposes /task and /agent_info via the controller.")
    print("Start the AgentBeats controller instead (`agentbeats run_ctrl`).")
    print(f"It will proxy to this agent at {host}:{port} when needed.")
