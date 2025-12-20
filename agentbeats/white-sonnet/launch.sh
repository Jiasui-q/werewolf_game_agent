#!/bin/bash
cd "$(dirname "$0")"

# set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=agentbeats-white-sonnet.yarralytics.bh
export ROLE=white
export PORT=8013
export AGENT_MODEL=anthropic/claude-sonnet-4.5

# launch agentbeats controller
agentbeats run_ctrl
