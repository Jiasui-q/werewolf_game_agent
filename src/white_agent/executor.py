import uvicorn
import tomllib
import os

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, SendMessageSuccessResponse, Message
from a2a.utils import new_agent_text_message
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler


from src.white_agent.agent import WhiteAgent, DEFAULT_MODEL

class WerewolfWhiteAgentExecutor(AgentExecutor):
    def __init__(self, agent: WhiteAgent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        context_id = context.context_id
        skip_response = (context.message.metadata or {}).get("skip_response", False)
        print(f"ctx: {context_id} | skip_response: {skip_response}")
        print(">>> " + user_input)
        statement = await self.agent.handle(context_id, user_input, skip_response=skip_response)
        if not skip_response:
            print("<<< " + statement)
        
        print("")
        await event_queue.enqueue_event(
            new_agent_text_message(
                statement, context_id=context.context_id
            )
        )

    async def cancel(self, context, event_queue) -> None:
        raise NotImplementedError


def load_agent_card_toml(agent_name):
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)


def start_white_agent(model=DEFAULT_MODEL, host: str = "0.0.0.0", port: int = 9002) -> None:
    print("Starting white agent...")
    agent_card_dict = load_agent_card_toml("werewolf_white_agent")
    agent_card_dict["name"] = f"werewolf_player_{model.replace('/', '_')}"
    agent_card_dict["url"] = os.getenv("AGENT_URL") or f"http://{host}:{port}"
    
    agent = WhiteAgent(model=model)
    
    request_handler = DefaultRequestHandler(
        agent_executor=WerewolfWhiteAgentExecutor(agent),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
