#!/usr/bin/env bash
set -euo pipefail

# Start the Tau-Bench-style Werewolf evaluation so AgentBeats can launch it via the controller.
python main.py launch
