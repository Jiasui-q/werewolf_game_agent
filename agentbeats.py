#!/usr/bin/env python
"""Lightweight shim to mimic `agentbeats run_ctrl` locally."""

import argparse
import sys

from controller import run_ctrl


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agentbeats")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run_ctrl", help="Start the AgentBeats-compatible controller")

    args = parser.parse_args(argv)

    if args.command == "run_ctrl":
        run_ctrl()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
