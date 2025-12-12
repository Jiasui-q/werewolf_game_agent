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

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from werewolf_game_agent.white_agent import WhiteAgent, MODEL_NAME


CONTROLLER_URL = os.getenv("CONTROLLER_URL")


app = FastAPI(title="Werewolf Agent Controller")


class AgentInfo(BaseModel):
    name: str = "Werewolf White Agent"
    version: str = "0.1.0"
    model: str = MODEL_NAME
    description: str = (
        "LLM-driven Werewolf player that generates discussion statements and votes."
    )
    author: str = "Jovan"


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


@app.get("/gr/info")
def get_gr_info():
    """Provide a lightweight controller health/info response."""
    info = AgentInfo()
    return {
        "service": "Werewolf Game Agent",
        "platform": "AgentBeats",
        "status": "ready",
        "version": info.version,
    }


@app.get("/info")
def info(request: Request):
    """Legacy helper that AgentBeats sometimes hits directly."""
    info_payload = AgentInfo()
    controller_url = _resolve_controller_url(request)
    return {
        "service": "Werewolf Game Agent",
        "status": "ready",
        "version": info_payload.version,
        "agentCardUrl": f"{controller_url}/.well-known/agent-card.json",
        "controllerUrl": controller_url,
    }


@app.get("/status")
def status():
    """Basic status endpoint used by AgentBeats."""
    return {"status": "ready", "agent": "Werewolf Game Agent"}


@app.get("/agent-card")
def agent_card():
    """Return the JSON payload used by the AgentBeats card display."""
    info = AgentInfo()
    return {
        "name": info.name,
        "description": info.description,
        "version": info.version,
        "capabilities": {
            "streaming": False,
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
        },
        "skills": [
            {
                "id": "werewolf_assessment",
                "name": "Werewolf Game Assessment",
                "description": "Hosts a Werewolf evaluation loop with Gemini-powered agents.",
                "tags": ["agentbeats", "werewolf", "assessment"],
            }
        ],
    }


@app.get("/.well-known/agent-card.json")
def agent_card_manifest():
    """Provide the same agent card under the well-known path."""
    return JSONResponse(agent_card())


@app.get("/", include_in_schema=False)
def root():
    """Lightweight health response so the controller remains API-only."""
    return {"status": "ready"}


def _resolve_controller_url(request: Request) -> str:
    """Build the public controller base URL from headers or env vars."""
    if CONTROLLER_URL:
        return CONTROLLER_URL.rstrip("/")

    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        host = request.url.hostname
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    return f"{scheme}://{host}"


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

    uvicorn.run("werewolf_game_agent.controller:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run_ctrl()
