#!/bin/bash

# set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=agentbeats-green.yarralytics.bh
export ROLE=green
export PORT=8010

# launch agentbeats controller
agentbeats run_ctrl
