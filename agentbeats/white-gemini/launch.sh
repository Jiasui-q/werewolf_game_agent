#!/bin/bash
cd "$(dirname "$0")"

# set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=agentbeats-white-gemini.yarralytics.bh
export ROLE=white
export PORT=8011
export AGENT_MODEL=google/gemini-3-flash-preview

# launch agentbeats controller
agentbeats run_ctrl
