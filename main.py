import argparse

from werewolf_game_agent.launcher import launch_evaluation


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Werewolf evaluation scenario in Tau-Bench style."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    launch_parser = subparsers.add_parser(
        "launch", help="Run a complete Werewolf evaluation."
    )
    launch_parser.add_argument(
        "--players",
        nargs="+",
        help="Explicit list of player names to include in the match.",
    )

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.command == "launch":
        launch_evaluation(args.players)


if __name__ == "__main__":
    main()
