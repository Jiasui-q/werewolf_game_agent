import random
from white_agent import WhiteAgent

class Player:
    def __init__(self, name, role, all_player_names):
        self.name = name
        self.role = role
        self.is_alive = True
        self.agent_logic = WhiteAgent(name, role, all_player_names)
        # memory of seer/medic actions
        self.last_seen = None
        self.protected = False

    def __repr__(self):
        status = "Alive" if self.is_alive else "Dead"
        return f"{self.name} ({self.role}, {status})"

class GameEnvironment:
    def __init__(self, player_names):
        self.players = []
        self.game_over = False
        self.winner = None
        self.game_log = []
        self._assign_roles(player_names)

    def _assign_roles(self, player_names):
        # Example 5-player setup: 2 special roles + 1 wolf + villagers
        roles = ["Werewolf", "Seer", "Medic", "Villager", "Villager"]
        random.shuffle(roles)
        for name, role in zip(player_names, roles):
            self.players.append(Player(name, role, player_names))
        print("--- Roles have been assigned secretly ---")
        print(self.players)

    # ---------- DAY PHASE ----------
    def run_day_phase(self):
        print("The sun rises. All players gather to discuss.")
        living_players = [p for p in self.players if p.is_alive]
        discussion_log = []

        print("\n--- Discussion Begins ---")
        for speaker in living_players:
            current_history = "\n".join(discussion_log) if discussion_log else "The discussion has just started."
            statement = speaker.agent_logic.generate_statement(current_history)
            full_statement = f"{speaker.name}: \"{statement}\""
            print(full_statement)
            discussion_log.append(full_statement)

        print("\n--- Voting Begins ---")
        final_discussion_history = "\n".join(discussion_log)
        votes = {}
        for voter in living_players:
            possible_targets = [p.name for p in living_players if p != voter]
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

    # ---------- NIGHT PHASE ----------
    def run_night_phase(self):
        print("\nThe sun sets. Night falls...")
        for p in self.players:
            p.protected = False  # reset protection each night

        living_players = [p for p in self.players if p.is_alive]
        werewolves = [p for p in living_players if p.role == "Werewolf"]
        seers = [p for p in living_players if p.role == "Seer"]
        medics = [p for p in living_players if p.role == "Medic"]
        villagers = [p for p in living_players if p.role not in ["Werewolf"]]

        # --- Werewolves choose target ---
        target = None
        if werewolves:
            potential_targets = [p for p in living_players if p.role != "Werewolf"]
            target = random.choice(potential_targets) if potential_targets else None
            if target:
                print("(Werewolves have chosen their target.)")

        # --- Seer inspects a player ---
        if seers:
            seer = seers[0]
            if seer.is_alive:
                inspectable = [p for p in living_players if p != seer]
                chosen = random.choice(inspectable)
                seer.last_seen = (chosen.name, chosen.role)
                print(f"(Seer learns privately that {chosen.name} is a {chosen.role}.)")
                self.game_log.append(f"SEER_SEES:{seer.name}:{chosen.name}:{chosen.role}")

        # --- Medic protects someone ---
        if medics:
            medic = medics[0]
            if medic.is_alive:
                protectable = [p for p in living_players]
                protected = random.choice(protectable)
                protected.protected = True
                print(f"(Medic protects {protected.name} tonight.)")
                self.game_log.append(f"MEDIC_PROTECTS:{medic.name}:{protected.name}")

        # --- Apply werewolf attack (unless protected) ---
        if target and not target.protected:
            target.is_alive = False
            print(f"The werewolves have killed {target.name}!")
            self.game_log.append(f"KILLED:{target.name}:{target.role}")
        elif target and target.protected:
            print(f"The werewolves tried to kill {target.name}, but they were saved by the Medic!")
            self.game_log.append(f"SAVED:{target.name}")

    # ---------- CHECK GAME STATUS ----------
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

    # ---------- PERFORMANCE REPORT ----------
    def run_evaluation(self):
        print("\n--- PERFORMANCE EVALUATION ---")
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
        for name, r in reports.items():
            print(f"\nPlayer: {name} ({r['role']})")
            print(f"  - Team Win: {'Yes' if r['team_win'] else 'No'}")
            print(f"  - Suspicion Score: {r['suspicion_score']}")
            if 'voting_accuracy' in r:
                print(f"  - Voting Accuracy: {r['voting_accuracy']:.2f}")

    # ---------- MAIN LOOP ----------
    def run_game(self):
        day = 1
        while not self.game_over:
            print(f"\n=== DAY {day} ===")
            self.run_day_phase()
            self.check_game_over()
            if self.game_over: break
            print(f"\n=== NIGHT {day} ===")
            self.run_night_phase()
            self.check_game_over()
            if self.game_over: break
            day += 1
        print(f"\n--- GAME OVER ---")
        print(f"The winner is: {self.winner}!")
        self.run_evaluation()
