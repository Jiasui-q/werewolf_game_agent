import time
import os
import tomllib
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from a2a.utils import new_agent_text_message
from src.my_util import parse_tags

from src.green_agent.agent import AsyncGameEnvironment


class WerewolfGreenAgentExecutor(AgentExecutor):
    def __init__(self):
        pass

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("Green agent: Received a task, parsing...")
        user_input = context.get_user_input()
        tags = parse_tags(user_input)
        white_agent_url = tags.get("white_agent_url")
        
        if not white_agent_url:
            print("Error: No white_agent_url provided.")
            return

        print(f"Agent URLs: {white_agent_url}")
        
        print("Green agent: Starting Werewolf Game Environment...")
        timestamp_started = time.time()
        
        env = AsyncGameEnvironment([white_agent_url])
        winner = await env.run_game()
        
        metrics = {
            "time_used": time.time() - timestamp_started,
            "winner": winner,
            "reports": env.get_reports(),
        }
        

        result_emoji = "🐺" if winner == "Werewolves" else "🛖"
        player_summary = "\n".join(f" - {p}" for p in env.players)
        summary_msg = (
            f"Finished.\n"
            f"Winner: {result_emoji} {winner}\n"
            f"Players:\n{player_summary}\n" 
            f"Metrics: {metrics}\n"
        )

        print(summary_msg)
        await event_queue.enqueue_event(new_agent_text_message(summary_msg))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError



def load_agent_card_toml(agent_name):
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)
    
def start_green_agent(agent_name="werewolf_green_agent", host="0.0.0.0", port=9001):
    print("Starting green agent...")
    agent_card_dict = load_agent_card_toml(agent_name)

    agent_card_dict["url"] = os.getenv("AGENT_URL") or f"http://{host}:{port}"

    request_handler = DefaultRequestHandler(
        agent_executor=WerewolfGreenAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
