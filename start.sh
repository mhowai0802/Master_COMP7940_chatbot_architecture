#!/bin/bash
# Start the bot in the background
python main.py &

# Start Flask on the port specified by Render
# The --no-debugger and --no-reload flags disable development features
export FLASK_APP=web_server.py
flask run --host=0.0.0.0 --port=${PORT:-10000} --no-debugger --no-reload