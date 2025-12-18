#!/bin/bash
cd "$(dirname "$0")"

# entrypoint for green agent

cd ../..
python main.py run
