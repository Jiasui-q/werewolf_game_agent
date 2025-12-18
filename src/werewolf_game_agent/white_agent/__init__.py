import dotenv
dotenv.load_dotenv()

import os
import random

from openai import OpenAI

# Default to the provided OpenRouter key but allow overriding via env var.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Reuse models across calls. Choose an available model that supports generateContent.
MODEL_NAME = "google/gemini-2.0-flash-001"


class WhiteAgent:
    def __init__(self, name, role, all_player_names):
        self.name = name
        self.role = role
        self.all_player_names = all_player_names

    def generate_statement(self, discussion_history):
        """Asks the LLM to generate a statement for the day's discussion."""

        prompt = f"""
        You are in a game of Werewolf. Your name is {self.name} and your secret role is {self.role}.
        The other players are: {", ".join(self.all_player_names)}.

        Here is the discussion so far:
        {discussion_history}

        What is your statement? Based on your role and the conversation, you can accuse someone, defend yourself, or try to guide the conversation.
        Keep your statement to 1-2 sentences. Speak in the first person.
        """

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            statement = (response.choices[0].message.content or "").strip()
            return statement if statement else "..."
        except Exception as e:
            print(f"An error occurred during statement generation for {self.name}: {e}")
            return "..."  # Return a silent response if the API fails

    def decide_vote(self, discussion_history, possible_targets):
        """Asks the LLM to decide who to vote for."""

        prompt = f"""
        You are in a game of Werewolf. Your name is {self.name} and your secret role is {self.role}.
        The other players are: {", ".join(self.all_player_names)}.

        Here is the full discussion from today:
        {discussion_history}

        Based on this discussion and your secret role, it is now time to vote. Who do you want to eliminate?
        Reply with ONLY the name of your chosen target from this list: {", ".join(possible_targets)}.
        Do not include any punctuation or extra words.
        """

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            raw_vote = (response.choices[0].message.content or "").strip()
            voted_for = self._extract_target(raw_vote, possible_targets)
            if voted_for:
                print(f"[{self.name} as {self.role}] AI decided to vote for: {voted_for}")
                return voted_for
        except Exception as e:
            print(f"An error occurred during AI decision for {self.name}: {e}")
        # Fallback if parsing fails or an exception was raised
        fallback = random.choice(possible_targets)
        print(f"[{self.name} as {self.role}] Falling back to random vote: {fallback}")
        return fallback

    def _extract_target(self, raw_vote, possible_targets):
        """Try to map model text to a valid target."""
        if raw_vote in possible_targets:
            return raw_vote
        lower_vote = raw_vote.lower()
        for target in possible_targets:
            if target.lower() in lower_vote:
                return target
        return None
