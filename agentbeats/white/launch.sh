#!/bin/bash
cd "$(dirname "$0")"

# set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=agentbeats-white.yarralytics.bh
export ROLE=white
export PORT=8011

# launch agentbeats controller
agentbeats run_ctrl
