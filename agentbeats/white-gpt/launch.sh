#!/bin/bash
cd "$(dirname "$0")"

# set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=agentbeats-white-gpt.yarralytics.bh
export ROLE=white
export PORT=8012
export AGENT_MODEL=openai/gpt-5.2

# launch agentbeats controller
agentbeats run_ctrl
