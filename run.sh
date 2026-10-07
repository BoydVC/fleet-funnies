#!/usr/bin/env bash
# Start (or restart) Fleet Funnies on 127.0.0.1:4142 in the background.
cd "$(dirname "$0")"
pkill -f "fleet-funnies/server.py" 2>/dev/null; sleep 0.3
setsid nohup python3 "$PWD/server.py" > /tmp/fleet-funnies-server.log 2>&1 < /dev/null &
sleep 0.7; curl -s -o /dev/null -w "port 4142 -> HTTP %{http_code}\n" http://127.0.0.1:4142/
