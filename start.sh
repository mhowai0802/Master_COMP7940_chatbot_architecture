#!/bin/bash
# Start the bot in the background
python main.py &

# Start Flask on the port specified by Render
# The --no-debugger and --no-reload flags disable development features
export FLASK_APP=webserver.py
flask run --host=0.0.0.0 --port=${PORT:-8080} --no-debugger --no-reload