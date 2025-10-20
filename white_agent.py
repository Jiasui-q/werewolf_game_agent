import os
import json
import random
from groq import Groq

client = Groq(api_key=os.getenv("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")) # Use Groq key

class WhiteAgent:
    def __init__(self, name, role, all_player_names):
        self.name = name
        self.role = role
        self.all_player_names = all_player_names

    def generate_statement(self, discussion_history):
        """Asks the LLM to generate a statement for the day's discussion."""

        prompt = f"""
        You are in a game of Werewolf. Your name is {self.name} and your secret role is {self.role}.
        The other players are: {', '.join(self.all_player_names)}.

        Here is the discussion so far:
        {discussion_history}

        What is your statement? Based on your role and the conversation, you can accuse someone, defend yourself, or try to guide the conversation.
        Keep your statement to 1-2 sentences. Speak in the first person.
        """

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8 # Allow for more creative/varied responses
            )
            statement = response.choices[0].message.content
            return statement.strip()
        except Exception as e:
            print(f"An error occurred during statement generation for {self.name}: {e}")
            return "..." # Return a silent response if the API fails

    def decide_vote(self, discussion_history, possible_targets):
        """Asks the LLM to decide who to vote for using tool calling."""

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "vote",
                    "description": "Casts a vote for a player to be eliminated.",
                    "parameters": {
                        "type": "object",
                        "properties": { "player_name": { "type": "string", "description": "The name of the player to vote for.", "enum": possible_targets } },
                        "required": ["player_name"]
                    }
                }
            }
        ]

        prompt = f"""
        You are in a game of Werewolf. Your name is {self.name} and your secret role is {self.role}.
        The other players are: {', '.join(self.all_player_names)}.

        Here is the full discussion from today:
        {discussion_history}

        Based on this discussion and your secret role, it is now time to vote. Who do you want to eliminate?
        You MUST choose one person from this list: {', '.join(possible_targets)}.
        """

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "vote"}}
            )

            tool_call = response.choices[0].message.tool_calls[0]
            if tool_call.function.name == "vote":
                arguments = json.loads(tool_call.function.arguments)
                voted_for = arguments.get("player_name")
                print(f"[{self.name} as {self.role}] AI decided to vote for: {voted_for}")
                return voted_for
        except Exception as e:
            print(f"An error occurred during AI decision for {self.name}: {e}")
            return random.choice(possible_targets)