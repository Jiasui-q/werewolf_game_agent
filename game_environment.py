import random
from white_agent import WhiteAgent

class Player:
    def __init__(self, name, role, all_player_names):
        self.name = name
        self.role = role
        self.is_alive = True
        # Each player gets their own AI brain
        self.agent_logic = WhiteAgent(name, role, all_player_names)

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
        roles = ["Werewolf", "Villager", "Villager", "Villager", "Villager"]
        random.shuffle(roles)
        for name, role in zip(player_names, roles):
            self.players.append(Player(name, role, player_names))
        print("--- Roles have been assigned secretly ---")
        print(self.players)

    def run_day_phase(self, day_number):
        """Manages the full discussion and voting phase."""
        print("The sun rises. All players gather to discuss.")

        living_players = [p for p in self.players if p.is_alive]
        discussion_log = [] # This will store the conversation as it happens

        # --- Discussion Phase ---
        print("\n--- Discussion Begins ---")
        # Let players speak one by one
        for speaker in living_players:
            # The history passed to each agent is what was said *before* their turn
            current_history = "\n".join(discussion_log) if discussion_log else "The discussion has just started."

            # Call the new method to get the agent's statement
            statement = speaker.agent_logic.generate_statement(current_history, day_number)

            # Format and record the statement
            full_statement = f"{speaker.name}: \"{statement}\""
            print(full_statement)
            discussion_log.append(full_statement)

        # --- Voting Phase ---
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

        # --- Vote Tally ---
        if not votes:
            print("No votes were cast. No one is eliminated.")
            return

        max_votes = max(votes.values())
        eliminated_players = [name for name, count in votes.items() if count == max_votes]

        if len(eliminated_players) == 1:
            eliminated_name = eliminated_players[0]
            for p in self.players:
                if p.name == eliminated_name:
                    p.is_alive = False
                    print(f"\nThe town has eliminated {p.name}. They were a {p.role}.")
                    self.game_log.append(f"ELIMINATED:{p.name}:{p.role}")
                    break
        else:
            # Handle ties
            print(f"\nThere was a tie in the vote between: {', '.join(eliminated_players)}. No one is eliminated.")

    def run_night_phase(self):
        print("The sun sets. It is now nighttime.")
        living_players = [p for p in self.players if p.is_alive]
        werewolves = [p for p in self.players if p.role == "Werewolf" and p.is_alive]
        villagers = [p for p in living_players if p.role != "Werewolf"]
        if werewolves and villagers:
            target = random.choice(villagers)
            target.is_alive = False
            print(f"The werewolves have chosen their target. A player has been eliminated.")
            self.game_log.append(f"KILLED:{target.name}:{target.role}")

    def check_game_over(self):
        living_players = [p for p in self.players if p.is_alive]
        num_werewolves = len([p for p in living_players if p.role == "Werewolf"])
        num_villagers = len(living_players) - num_werewolves
        if num_werewolves == 0:
            self.game_over = True
            self.winner = "Villagers"
        elif num_werewolves >= num_villagers:
            self.game_over = True
            self.winner = "Werewolves"

    def run_evaluation(self):
        """Analyzes the game log and prints a performance report for each player."""
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

    def run_game(self):
        day_number = 1
        while not self.game_over:
            print(f"\n--- Day {day_number} ---")
            self.run_day_phase(day_number)
            self.check_game_over()
            if self.game_over: break
            print(f"\n--- Night {day_number} ---")
            self.run_night_phase()
            self.check_game_over()
            if self.game_over: break
            day_number += 1
        print(f"\n--- GAME OVER ---")
        print(f"The winner is: {self.winner}!")
        self.run_evaluation()