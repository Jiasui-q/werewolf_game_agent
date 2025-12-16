"""Green agent implementation - manages assessment and evaluation for Werewolf Game."""

import uvicorn
import tomllib
import dotenv
import time
import os
import random
from typing import List

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, SendMessageSuccessResponse, Message
from a2a.utils import new_agent_text_message, get_text_parts
from src.my_util import parse_tags, my_a2a

# Import the local WhiteAgent for NPC players
from werewolf_game_agent.white_agent import WhiteAgent

dotenv.load_dotenv()


def load_agent_card_toml(agent_name):
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)


class AsyncPlayer:
    def __init__(self, name, role, all_player_names, is_remote=False, white_agent_url=None):
        self.name = name
        self.role = role
        self.is_alive = True
        self.is_remote = is_remote
        self.white_agent_url = white_agent_url
        self.last_seen = None
        self.protected = False
        
        if not is_remote:
            self.agent_logic = WhiteAgent(name, role, all_player_names)
        else:
            self.agent_logic = None  # Logic is handled via remote calls

    def __repr__(self):
        status = "Alive" if self.is_alive else "Dead"
        remote_tag = "[Remote]" if self.is_remote else "[NPC]"
        return f"{self.name} ({self.role}, {status}) {remote_tag}"


class AsyncGameEnvironment:
    def __init__(self, player_names: List[str], remote_agent_url: str, remote_player_name: str = "Alice"):
        self.players: List[AsyncPlayer] = []
        self.game_over = False
        self.winner = None
        self.game_log: List[str] = []
        self.remote_agent_url = remote_agent_url
        self.remote_player_name = remote_player_name
        self._assign_roles(player_names)

    def _assign_roles(self, player_names):
        # Example 5-player setup: 2 special roles + 1 wolf + villagers
        # Ensure remote player is in the list
        if self.remote_player_name not in player_names:
            # If the requested name isn't in the list, replace the first one
            player_names[0] = self.remote_player_name

        roles = ["Werewolf", "Seer", "Medic", "Villager", "Villager"]
        # Ensure we have enough roles for players
        if len(player_names) > len(roles):
            roles.extend(["Villager"] * (len(player_names) - len(roles)))
        elif len(player_names) < len(roles):
            roles = roles[:len(player_names)]
            
        random.shuffle(roles)
        
        for name, role in zip(player_names, roles):
            is_remote = (name == self.remote_player_name)
            self.players.append(AsyncPlayer(name, role, player_names, is_remote, self.remote_agent_url))
            
        print("--- Roles have been assigned secretly ---")
        for p in self.players:
            print(p)

    async def _get_remote_response(self, prompt: str, context_id: str = None) -> str:
        print(f"@@@ Green agent: Sending message to remote white agent...\n{prompt[:200]}...")
        white_agent_response = await my_a2a.send_message(
            self.remote_agent_url, prompt, context_id=context_id
        )
        res_root = white_agent_response.root
        assert isinstance(res_root, SendMessageSuccessResponse)
        res_result = res_root.result
        assert isinstance(res_result, Message)
        
        text_parts = get_text_parts(res_result.parts)
        if not text_parts:
            return "..."
        response_text = text_parts[0]
        print(f"@@@ White agent response:\n{response_text}")
        return response_text

    async def run_day_phase(self, day: int):
        print(f"\nThe sun rises (Day {day}). All players gather to discuss.")
        living_players = [p for p in self.players if p.is_alive]
        discussion_log = []

        print("\n--- Discussion Begins ---")
        for speaker in living_players:
            current_history = "\n".join(discussion_log) if discussion_log else "The discussion has just started."
            
            if speaker.is_remote:
                prompt = f"""
You are playing a game of Werewolf. It is Day {day}.
Your name is {speaker.name} and your secret role is {speaker.role}.
The other players are: {", ".join([p.name for p in self.players if p != speaker])}.

Here is the discussion so far:
{current_history}

What is your statement? Based on your role and the conversation, you can accuse someone, defend yourself, or try to guide the conversation.
Keep your statement to 1-2 sentences. Speak in the first person.
Response with just the statement.
"""
                statement = await self._get_remote_response(prompt)
            else:
                statement = speaker.agent_logic.generate_statement(current_history)
            
            full_statement = f"{speaker.name}: \"{statement}\""
            print(full_statement)
            discussion_log.append(full_statement)

        print("\n--- Voting Begins ---")
        final_discussion_history = "\n".join(discussion_log)
        votes = {}
        
        for voter in living_players:
            possible_targets = [p.name for p in living_players if p != voter]
            
            if voter.is_remote:
                prompt = f"""
It is voting time on Day {day}.
Discussion history:
{final_discussion_history}

Who do you want to eliminate?
Reply with ONLY the name of your chosen target from this list: {", ".join(possible_targets)}.
"""
                raw_vote = await self._get_remote_response(prompt)
                # Simple extraction logic similar to WhiteAgent._extract_target
                voted_for = None
                clean_vote = raw_vote.strip()
                if clean_vote in possible_targets:
                    voted_for = clean_vote
                else:
                    # heuristic search
                    for t in possible_targets:
                        if t.lower() in clean_vote.lower():
                            voted_for = t
                            break
                if not voted_for:
                    voted_for = random.choice(possible_targets)
            else:
                voted_for = voter.agent_logic.decide_vote(final_discussion_history, possible_targets)
            
            if voted_for:
                print(f"{voter.name} votes for {voted_for}.")
                self.game_log.append(f"VOTE:{voter.name}:{voted_for}")
                votes[voted_for] = votes.get(voted_for, 0) + 1

        if not votes:
            print("No votes were cast. No one is eliminated.")
            return

        max_votes = max(votes.values())
        eliminated = [n for n, c in votes.items() if c == max_votes]
        
        if len(eliminated) == 1:
            name = eliminated[0]
            for p in self.players:
                if p.name == name:
                    p.is_alive = False
                    print(f"\nThe town has eliminated {p.name}. They were a {p.role}.")
                    self.game_log.append(f"ELIMINATED:{p.name}:{p.role}")
                    break
        else:
            print(f"\nThere was a tie between {', '.join(eliminated)}. No one is eliminated.")

    async def run_night_phase(self, day: int):
        print(f"\nThe sun sets (Night {day}). Night falls...")
        for p in self.players:
            p.protected = False

        living_players = [p for p in self.players if p.is_alive]
        werewolves = [p for p in living_players if p.role == "Werewolf"]
        seers = [p for p in living_players if p.role == "Seer"]
        medics = [p for p in living_players if p.role == "Medic"]
        
        # --- Werewolves choose target ---
        target = None
        if werewolves:
            potential_targets = [p for p in living_players if p.role != "Werewolf"]
            # Simplified: If remote is werewolf, we could ask them, but for now let's random or auto if multiple wolves
            # If the remote is the ONLY werewolf, we MUST ask them.
            active_wolves = [w for w in werewolves]
            remote_wolf = next((w for w in active_wolves if w.is_remote), None)
            
            if remote_wolf:
                prompt = f"""
It is Night {day}. You are a Werewolf.
Your fellow wolves are: {", ".join([w.name for w in active_wolves if w != remote_wolf])}
Valid targets: {", ".join([p.name for p in potential_targets])}

Who do you want to kill? Reply with ONLY the name.
"""
                raw_kill = await self._get_remote_response(prompt)
                # extraction
                clean_kill = raw_kill.strip()
                for t in potential_targets:
                    if t.name == clean_kill or t.name.lower() in clean_kill.lower():
                        target = t
                        break
                if not target and potential_targets:
                     target = random.choice(potential_targets)
            else:
                if potential_targets:
                    target = random.choice(potential_targets)
            
            if target:
                print("(Werewolves have chosen their target.)")

        # --- Seer inspects ---
        if seers:
            seer = seers[0]
            inspectable = [p for p in living_players if p != seer]
            if inspectable:
                if seer.is_remote:
                    prompt = f"""
It is Night {day}. You are the Seer.
Valid targets to inspect: {", ".join([p.name for p in inspectable])}
Who do you want to inspect? Reply with ONLY the name.
"""
                    raw_inspect = await self._get_remote_response(prompt)
                    chosen = None
                    for t in inspectable:
                        if t.name in raw_inspect or t.name.lower() in raw_inspect.lower():
                            chosen = t
                            break
                    if not chosen: chosen = random.choice(inspectable)
                else:
                    chosen = random.choice(inspectable)
                
                seer.last_seen = (chosen.name, chosen.role)
                print(f"(Seer learns privately that {chosen.name} is a {chosen.role}.)")
                self.game_log.append(f"SEER_SEES:{seer.name}:{chosen.name}:{chosen.role}")
                
                # Notify remote seer of result
                if seer.is_remote:
                    await self._get_remote_response(f"Result: {chosen.name} is a {chosen.role}. (Ack)")

        # --- Medic protects ---
        if medics:
            medic = medics[0]
            protectable = [p for p in living_players]
            if medic.is_remote:
                prompt = f"""
It is Night {day}. You are the Medic.
Who do you want to protect? Reply with ONLY the name.
Possible: {", ".join([p.name for p in protectable])}
"""
                raw_protect = await self._get_remote_response(prompt)
                protected = None
                for t in protectable:
                    if t.name in raw_protect or t.name.lower() in raw_protect.lower():
                        protected = t
                        break
                if not protected: protected = random.choice(protectable)
            else:
                protected = random.choice(protectable)
                
            protected.protected = True
            print(f"(Medic protects {protected.name} tonight.)")
            self.game_log.append(f"MEDIC_PROTECTS:{medic.name}:{protected.name}")

        # --- Apply kill ---
        if target and not target.protected:
            target.is_alive = False
            print(f"The werewolves have killed {target.name}!")
            self.game_log.append(f"KILLED:{target.name}:{target.role}")
        elif target and target.protected:
            print(f"The werewolves tried to kill {target.name}, but they were saved by the Medic!")
            self.game_log.append(f"SAVED:{target.name}")

    def check_game_over(self):
        living = [p for p in self.players if p.is_alive]
        num_wolves = len([p for p in living if p.role == "Werewolf"])
        num_others = len(living) - num_wolves
        if num_wolves == 0:
            self.game_over = True
            self.winner = "Villagers"
        elif num_wolves >= num_others:
            self.game_over = True
            self.winner = "Werewolves"

    async def run_game(self):
        day = 1
        while not self.game_over:
            print(f"\n=== DAY {day} ===")
            await self.run_day_phase(day)
            self.check_game_over()
            if self.game_over: break
            
            print(f"\n=== NIGHT {day} ===")
            await self.run_night_phase(day)
            self.check_game_over()
            if self.game_over: break
            
            day += 1
            
        print(f"\n--- GAME OVER ---")
        print(f"The winner is: {self.winner}!")
        return self.winner


class WerewolfGreenAgentExecutor(AgentExecutor):
    def __init__(self):
        pass

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("Green agent: Received a task, parsing...")
        user_input = context.get_user_input()
        tags = parse_tags(user_input)
        white_agent_url = tags.get("white_agent_url")
        # env_config_str = tags.get("env_config") # unused for now
        
        if not white_agent_url:
            print("Error: No white_agent_url provided.")
            return

        print(f"Target Agent URL: {white_agent_url}")
        
        # Default players if not in config
        player_names = ["Alice", "Bob", "Charlie", "David", "Eva"]
        
        print("Green agent: Starting Werewolf Game Environment...")
        timestamp_started = time.time()
        
        env = AsyncGameEnvironment(player_names, white_agent_url, remote_player_name="Alice")
        winner = await env.run_game()
        
        metrics = {
            "time_used": time.time() - timestamp_started,
            "winner": winner,
            "remote_player_role": next((p.role for p in env.players if p.is_remote), "Unknown"),
            "remote_player_won": False # TBD
        }
        
        # Determine if remote player won
        remote_p = next((p for p in env.players if p.is_remote), None)
        if remote_p:
            is_wolf = remote_p.role == "Werewolf"
            if (winner == "Werewolves" and is_wolf) or (winner == "Villagers" and not is_wolf):
                metrics["remote_player_won"] = True

        result_emoji = "✅" if metrics["remote_player_won"] else "❌"

        print(f"Finished. White agent success: {result_emoji}\nMetrics: {metrics}\n")
        await event_queue.enqueue_event(
            new_agent_text_message(
                f"Finished. White agent success: {result_emoji}\nMetrics: {metrics}\n"
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError


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
