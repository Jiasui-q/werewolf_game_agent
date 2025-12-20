"""Green agent implementation - manages assessment and evaluation for Werewolf Game."""

import asyncio
from uuid import uuid4
import random
from typing import List, Dict, Optional


from a2a.utils import get_message_text
from src.my_util import my_a2a

# Import the local WhiteAgent for NPC players
from werewolf_game_agent.white_agent import WhiteAgent
from src.white_agent.agent import WhiteAgent

DEFAULT_PLAYERS = ["Alice", "Bob", "Charlie", "David", "Eva", "Frank", "Grace", "Hannah", "Ian", "Judy"]
MIN_GAME_SIZE = 6

class AsyncPlayer:
    def __init__(self, name, role, agent_url=None):
        self.name = name
        self.role = role
        
        self.is_alive = True
        self.protected = False

        self.agent_url = agent_url
        self.is_remote = agent_url is not None

        self.agent = WhiteAgent() if not self.is_remote else None
        self.ctx_id = uuid4().hex if not self.is_remote else None

        
    def __repr__(self):
        status = "Alive" if self.is_alive else "Dead"
        remote_tag = "[Remote]" if self.is_remote else "[Local]"
        return f"{self.name} ({self.role}, {status}) {remote_tag}"
    
    async def send(self, message: str, skip_response=False):
        if self.is_remote:
            # make A2A call to remote agent
            metadata = {"skip_response": skip_response}
            response = await my_a2a.send_message(
                self.agent_url,
                message, 
                context_id=self.ctx_id, 
                metadata=metadata
            )

            # remember context id for future messages
            self.ctx_id = response.root.result.context_id
            return get_message_text(response.root.result)
        else:
            # use local agent instance
            return await self.agent.handle(
                self.ctx_id,
                message,
                skip_response=skip_response
            )


class AsyncGameEnvironment:
    def __init__(
        self,
        agent_urls: List[str],
        player_count = MIN_GAME_SIZE
    ):
        self.players: List[AsyncPlayer] = []

        self.game_over = False
        self.winner: Optional[str] = None

        self.game_log: List[str] = []
        self.history = []

        self._assign_roles(agent_urls, player_count)

    def _assign_roles(self, agent_urls: List[str], player_count) -> None:
        """Assign roles to all players"""
        remote_count = len(agent_urls)
        player_count = max(player_count, remote_count)
        if player_count > len(DEFAULT_PLAYERS):
            raise ValueError(f"Cannot support more than {len(DEFAULT_PLAYERS)} players.")
        npc_count = max(player_count - remote_count, 0)
        
        names = DEFAULT_PLAYERS[:player_count]
        roles = ["Werewolf", "Seer", "Medic"] + ["Villager"] * (player_count - 3)
        agent_urls = agent_urls + [None] * npc_count # pad for local players

        random.shuffle(roles)

        for name, role, agent_url in zip(names, roles, agent_urls):
            player = AsyncPlayer(
                name, role, agent_url
            )
            self.players.append(player)

        print("--- Roles have been assigned secretly ---")
        for p in self.players:
            print(p)


    async def run_day_phase(self, day: int):
        print(f"\nThe sun rises (Day {day}). All players gather to discuss.")
        living_players = [p for p in self.players if p.is_alive]
        discussion_log = []

        print("\n--- Discussion Begins ---")
        for speaker in living_players:
            current_history = "\n".join(discussion_log) if discussion_log else "The discussion has just started."
            
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
            statement = await speaker.send(prompt)
            
            full_statement = f"{speaker.name}: \"{statement}\""
            print(full_statement)
            discussion_log.append(full_statement)

        print("\n--- Voting Begins ---")
        final_discussion_history = "\n".join(discussion_log)
        votes = {}
        
        for voter in living_players:
            possible_targets = [p.name for p in living_players if p != voter]
            
            prompt = f"""
It is voting time on Day {day}.
Discussion history:
{final_discussion_history}

Who do you want to eliminate?
Reply with ONLY the name of your chosen target from this list: {", ".join(possible_targets)}.
"""
            raw_vote = await voter.send(prompt)
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
        werewolf = next(p for p in living_players if p.role == "Werewolf")
        seers = [p for p in living_players if p.role == "Seer"]
        medics = [p for p in living_players if p.role == "Medic"]
        
        # --- Werewolves choose target ---
        target = None
        potential_targets = [p for p in living_players if p.role != "Werewolf"]
        
        prompt = f"""
It is Night {day}. You are a Werewolf.
Valid targets: {", ".join([p.name for p in potential_targets])}

Who do you want to kill? Reply with ONLY the name.
"""
        raw_kill = await werewolf.send(prompt)
        # extraction
        clean_kill = raw_kill.strip()
        for t in potential_targets:
            if t.name == clean_kill or t.name.lower() in clean_kill.lower():
                target = t
                break
        if not target and potential_targets:
                target = random.choice(potential_targets)
        
        if target:
            print("(Werewolves have chosen their target.)")

        # --- Seer inspects ---
        if seers:
            seer = seers[0]
            inspectable = [p for p in living_players if p != seer]
            if inspectable:
                prompt = f"""
It is Night {day}. You are the Seer.
Valid targets to inspect: {", ".join([p.name for p in inspectable])}
Who do you want to inspect? Reply with ONLY the name.
"""
                raw_inspect = await seer.send(prompt)
                chosen = None
                for t in inspectable:
                    if t.name in raw_inspect or t.name.lower() in raw_inspect.lower():
                        chosen = t
                        break
                if not chosen: chosen = random.choice(inspectable)
                
                print(f"(Seer learns privately that {chosen.name} is a {chosen.role}.)")
                self.game_log.append(f"SEER_SEES:{seer.name}:{chosen.name}:{chosen.role}")
                
                # Notify remote seer of result
                await seer.send(f"Result: {chosen.name} is a {chosen.role}.", skip_response=True)

        # --- Medic protects ---
        if medics:
            medic = medics[0]
            protectable = [p for p in living_players]
            prompt = f"""
It is Night {day}. You are the Medic.
Who do you want to protect? Reply with ONLY the name.
Possible: {", ".join([p.name for p in protectable])}
"""
            raw_protect = await medic.send(prompt)
            protected = None
            for t in protectable:
                if t.name in raw_protect or t.name.lower() in raw_protect.lower():
                    protected = t
                    break
            if not protected: protected = random.choice(protectable)
                
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

    def get_reports(self):
        reports = {p.name: {'role': p.role,
                            'team_win': (self.winner == 'Werewolves' and p.role == 'Werewolf')
                                        or (self.winner == 'Villagers' and p.role != 'Werewolf')}
                   for p in self.players}
        for name in reports:
            reports[name]['suspicion_score'] = sum(1 for log in self.game_log
                                                   if log.startswith("VOTE:") and log.split(':')[2] == name)
        for voter in self.players:
            if voter.role != 'Werewolf':
                votes = [log for log in self.game_log if log.startswith(f"VOTE:{voter.name}:")]
                if votes:
                    correct = sum(1 for v in votes if
                                  reports[v.split(':')[2]]['role'] == 'Werewolf')
                    reports[voter.name]['voting_accuracy'] = correct / len(votes)
        return reports

    def run_evaluation(self):
        print("\n--- PERFORMANCE EVALUATION ---")
        reports = self.get_reports()
        for name, r in reports.items():
            print(f"\nPlayer: {name} ({r['role']})")
            print(f"  - Team Win: {'Yes' if r['team_win'] else 'No'}")
            print(f"  - Suspicion Score: {r['suspicion_score']}")
            if 'voting_accuracy' in r:
                print(f"  - Voting Accuracy: {r['voting_accuracy']:.2f}")

    @property
    def alive_players(self):
        return [p for p in self.players if p.is_alive]

    async def _broadcast(self, message: str, skip_response=False):
        """Send a message to all players concurrently."""
        tasks = []
        for player in self.players:
            if player.is_alive:
                tasks.append(player.send(message, skip_response=skip_response))
        return await asyncio.gather(*tasks)


    async def _phase_day_1(self):
        """
        Special handling for Day 1. 
        - Players are informed of their roles.
        - Players concurrently generate an initial statement.
        """

        # gather introductions
        async def _introduce(player: AsyncPlayer):
            other_players = ", ".join([p.name for p in self.players if p != player])
            role_message = (
                f"It is Day 1. Your name is {player.name} and your secret role is {player.role}.\n"
                f"The other players are: {other_players}.\n"
                "Make an opening statement to introduce yourself.\n"
            )
            statement = await player.send(role_message)
            return f"{player.name}: \"{statement}\""
        
        print(f"\nThe sun rises (Day 1). All players gather to discuss.")
        introductions = await asyncio.gather(*[_introduce(p) for p in self.alive_players])

        for intro in introductions:
            print(f">>> {intro}")

        # notify players of everyone elses introductions
        async def _notify_introductions(player: AsyncPlayer, idx: int):
            others_intro = "\n".join([intro for i, intro   in enumerate(introductions) if i != idx])
            notify_message = f"The other players introduce themselves as well.\n{others_intro}"
            await player.send(notify_message, skip_response=True)

        await asyncio.gather(*[_notify_introductions(p, i) for i, p in enumerate(self.alive_players)])

    async def _phase_night(self, day: int):
        """
        Conduct night phase.
        - Werewolves choose a target to kill.
        - Seer inspects a player.
        - Medic protects a player.
        - Apply night actions.
        - Players receive a night outcome summary.
        """

    async def _phase_day(self, day: int):
        """
        Conduct day phase.
        - Players concurrently generate statements.
        - Players receive all statements and cast a vote.
        """

    async def run_game(self):
        day = 1
        while not self.game_over:
            if day == 1:
                await self._phase_day_1()
            else:
                await self._phase_day(day)
            self.check_game_over()
            if self.game_over: break

            await self._phase_night(day)
            self.check_game_over()
            if self.game_over: break
            day += 1
        
        print("\n--- GAME OVER ---")
        print(f"The winner is: {self.winner}!")
        self.run_evaluation()



    async def _run_game(self):
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
        self.run_evaluation()
        return self.winner
