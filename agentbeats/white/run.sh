#!/bin/bash
cd "$(dirname "$0")"

# entrypoint for white agent

cd ../..
python main.py run
