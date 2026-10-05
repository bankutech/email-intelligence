#!/bin/bash
# Start the background polling worker
python main.py run &

# Start the web dashboard (FastAPI)
python main.py dashboard
