from game_environment import GameEnvironment

if __name__ == "__main__":
    # Define the players for our game
    player_names = ["Alice", "Bob", "Charlie", "David", "Eva"]

    # Create an instance of our environment
    game = GameEnvironment(player_names)

    # Start the game!
    game.run_game()
