import dotenv
dotenv.load_dotenv()

from collections import defaultdict
import os

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, SendMessageSuccessResponse, Message
from a2a.utils import new_agent_text_message

from openai import AsyncOpenAI

DEFAULT_MODEL = "google/gemini-2.0-flash-001"
DEFAULT_SYSTEM_PROMPT = (
    "You are playing a game of Werewolf. Follow the instructions provided by the user exactly. "
    "Keep your statements short and speak in the first person. "
    "When asked to pick a player, respond with only the player's name. "
)

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
    
    async def handle(self, ctx_id: str, message: str, skip_response: bool = False) -> str:
        self.add(ctx_id, "user", message)
        if skip_response:
            return ""
        return await self.respond(ctx_id)
