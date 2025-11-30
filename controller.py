"""
AgentBeats-compatible controller for the Werewolf agent.

Endpoints:
- GET /agent_info : basic metadata for platform checks.
- POST /task : runs statement and (optional) vote using WhiteAgent.
- POST /reset : clears in-memory logs/state.
- GET /logs : returns recent task interactions.
"""

import os
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from white_agent import WhiteAgent, MODEL_NAME


app = FastAPI(title="Werewolf Agent Controller")


class AgentInfo(BaseModel):
    name: str = "Werewolf White Agent"
    version: str = "0.1.0"
    model: str = MODEL_NAME
    description: str = (
        "LLM-driven Werewolf player that generates discussion statements and votes."
    )
    author: str = "Codex"


class TaskRequest(BaseModel):
    player_name: str = Field(..., description="Current agent/player name")
    role: str = Field(..., description="Secret role assigned to this player")
    all_players: List[str] = Field(
        ..., description="All players' names in the match, including this agent"
    )
    discussion_history: str = Field(
        default="",
        description="Transcript of the day's discussion. Provide empty to start.",
    )
    possible_targets: Optional[List[str]] = Field(
        default=None,
        description="Names this agent may vote for. If omitted, no vote is returned.",
    )


class TaskResponse(BaseModel):
    statement: str
    vote: Optional[str] = None
    model: str = MODEL_NAME


# In-memory log buffer for /logs. Kept small to avoid unbounded memory.
MAX_LOGS = 50
logs: List[dict] = []


@app.get("/agent_info", response_model=AgentInfo)
def agent_info():
    return AgentInfo()


@app.post("/task", response_model=TaskResponse)
def handle_task(req: TaskRequest):
    agent = WhiteAgent(req.player_name, req.role, req.all_players)
    discussion = req.discussion_history or "The discussion has just started."
    statement = agent.generate_statement(discussion)

    vote = None
    if req.possible_targets:
        vote = agent.decide_vote(discussion, req.possible_targets)

    entry = {
        "player": req.player_name,
        "role": req.role,
        "statement": statement,
        "vote": vote,
        "discussion_history": req.discussion_history,
    }
    logs.append(entry)
    if len(logs) > MAX_LOGS:
        logs.pop(0)

    return TaskResponse(statement=statement, vote=vote)


@app.post("/reset")
def reset_state():
    logs.clear()
    return {"status": "ok", "message": "State reset."}


@app.get("/logs")
def get_logs():
    return {"logs": logs}


def run_ctrl():
    """Start the controller with uvicorn (AgentBeats expects port 8010)."""
    import uvicorn

    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8010"))

    https_enabled = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
    cloudrun_host = os.getenv("CLOUDRUN_HOST")
    role = os.getenv("ROLE")

    print(f"Starting controller on http://{host}:{port}")
    if https_enabled and cloudrun_host:
        print(f"External URL: https://{cloudrun_host}")
    if role:
        print(f"Agent role tag: {role}")

    uvicorn.run("controller:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run_ctrl()
