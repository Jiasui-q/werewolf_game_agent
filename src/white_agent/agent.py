import uvicorn
import tomllib
import os

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, SendMessageSuccessResponse, Message
from a2a.utils import new_agent_text_message, get_text_parts
from src.my_util import parse_tags, my_a2a

from werewolf_game_agent.white_agent import client, MODEL_NAME


def load_agent_card_toml(agent_name):
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)

class WerewolfWhiteAgentExecutor(AgentExecutor):
    def __init__(self):
        pass

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("White agent: Received a task, parsing...")
        user_input = context.get_user_input()
        tags = parse_tags(user_input)
        prompt = tags.get("prompt")

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            statement = (response.choices[0].message.content or "").strip()
            if not statement:
                statement = "..."
        except Exception as e:
            print(f"An error occurred during statement generation: {e}")
            statement = "..."  # Return a silent response if the API fails
        
        print(f"White agent: Generated response: {statement[:200]}...")
        await event_queue.enqueue_event(
            new_agent_text_message(
                statement, context_id=context.context_id
            )
        )

    async def cancel(self, context, event_queue) -> None:
        raise NotImplementedError


def start_white_agent(agent_name="werewolf_white_agent", host: str = "0.0.0.0", port: int = 9002) -> None:
    print("Starting white agent...")
    agent_card_dict = load_agent_card_toml(agent_name)

    agent_card_dict["url"] = os.getenv("AGENT_URL") or f"http://{host}:{port}"

    request_handler = DefaultRequestHandler(
        agent_executor=WerewolfWhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
