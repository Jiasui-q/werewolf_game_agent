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

    def run_day_phase(self, day_number):
        """Manages the full discussion and voting phase."""
        print("The sun rises. All players gather to discuss.")
        living_players = [p for p in self.players if p.is_alive]
        discussion_log = []

        print("\n--- Discussion Begins ---")
        for speaker in living_players:
            current_history = "\n".join(discussion_log) if discussion_log else "The discussion has just started."

            # Call the new method to get the agent's statement
            statement = speaker.agent_logic.generate_statement(current_history, day_number)

            # Format and record the statement
            full_statement = f"{speaker.name}: \"{statement}\""
            print(full_statement)
            discussion_log.append(full_statement)

        print("\n--- Voting Begins ---")
        final_discussion_history = "\n".join(discussion_log)
        votes = {}
        for voter in living_players:
            possible_targets = [p.name for p in living_players if p != voter]

            # Pass the complete, dynamic discussion history to the voting logic
            voted_for = voter.agent_logic.decide_vote(final_discussion_history, possible_targets, day_number)

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

        player_reports = {}
        for p in self.players:
            agent_memory = p.agent_logic.memory
            player_reports[p.name] = {
                'role': p.role,
                'team_win': (self.winner == 'Werewolves' and p.role == 'Werewolf') or (self.winner == 'Villagers' and p.role != 'Werewolf'),
                'memory': agent_memory
            }
        #{p.name: {'role': p.role, 'team_win': (self.winner == 'Werewolves' and p.role == 'Werewolf') or (self.winner == 'Villagers' and p.role != 'Werewolf')} for p in self.players}

        # Calculate Suspicion Score (how many votes each player received)
        for p_name in player_reports:
            player_reports[p_name]['suspicion_score'] = sum(1 for log in self.game_log if log.startswith("VOTE:") and log.split(':')[2] == p_name)

        # Calculate Villager Voting Accuracy
        for voter in self.players:
            if voter.role != 'Werewolf':
                correct_votes = 0
                total_votes = 0
                for log in self.game_log:
                    if log.startswith(f"VOTE:{voter.name}:"):
                        total_votes += 1
                        voted_for_name = log.split(':')[2]
                        voted_for_role = player_reports[voted_for_name]['role']
                        if voted_for_role == 'Werewolf':
                            correct_votes += 1
                accuracy = (correct_votes / total_votes) if total_votes > 0 else 'N/A'
                player_reports[voter.name]['voting_accuracy'] = accuracy

        # Print the final report card
        for name, report in player_reports.items():
            memory = report['memory']

            #1. Vote consistency:
            inconsistencies = 0
            for day, voted_for in memory['votes_by_day'].items():
                if voted_for in memory['suspection_map'] and memory['suspection_map'][voted_for] < 0: 
                    inconsstencies += 1
            
            report['vote_inconsistency'] = inconsistencies

            #2. Bluff duration (wolves only) // measure how long wolves' bluff stands
            if report['role'] == 'Werewolf':
                report['bluff_duration'] = sum(1 for claim in report['memory']['claims_made'] if 'not a werewolf' in claim.lower())

            #3. Suspection score on actual wolves (for villagers):
            true_wolves = [p.name for p in self.players if p.role == 'Werewolf']
            suspection_map = report['memory']['suspection_map']
            report['total_wolf_suspection'] = sum(suspection_map.get(w, 0) for w in true_wolves)

            print(f"\nPlayer: {name} ({report['role']})")
            print(f"  - Team Win: {'Yes' if report['team_win'] else 'No'}")
            print(f"  - Voting Inconsistencies: {report.get('vote_inconsistency', 0)}")
            print(f"  - Bluff Duration: {report.get('bluff_duration', 'N/A')}")
            print(f"  - Suspicion on Wolves: {report.get('total_wolf_suspicion', 'N/A')}")
            if 'voting_accuracy' in report:
                print(f"  - Voting Accuracy: {report['voting_accuracy']}")

    # ---------- MAIN LOOP ----------
    def run_game(self):
        day = 1
        while not self.game_over:
            print(f"\n--- Day {day} ---")
            self.run_day_phase(day)
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
