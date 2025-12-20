import dotenv
dotenv.load_dotenv()

from collections import defaultdict
import uvicorn
import tomllib
import os

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, SendMessageSuccessResponse, Message
from a2a.utils import new_agent_text_message

from openai import AsyncOpenAI

DEFAULT_MODEL = "google/gemini-2.0-flash-001"
DEFAULT_SYSTEM_PROMPT = "You are playing a game of Werewolf. Follow the instructions provided by the user exactly."

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

class WhiteAgent:
    def __init__(self, system_prompt=DEFAULT_SYSTEM_PROMPT, model=DEFAULT_MODEL):
        self.messages = defaultdict(lambda: [{"role": "system", "content": system_prompt}])
        self.model = model
    
    def add(self, ctx_id: str, role: str, content: str):
        self.messages[ctx_id].append({"role": role, "content": content})
    
    async def respond(self, ctx_id: str) -> str:
        response = await client.chat.completions.create(
            model=self.model,
            messages=self.messages[ctx_id],
            temperature=0,
        )
        statement = (response.choices[0].message.content or "").strip()
        self.add(ctx_id, "assistant", statement)
        return statement


class WerewolfWhiteAgentExecutor(AgentExecutor):
    def __init__(self, agent: WhiteAgent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        context_id = context.context_id
        skip_response = (context.message.metadata or {}).get("skip_response", False)
        print(f"ctx: {context_id} | skip_response: {skip_response}")
        print(">>> " + user_input)

        self.agent.add(context_id, "user", user_input)

        if skip_response: 
            statement = ""
        else:
            statement = await self.agent.respond(context_id)
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
