#!/usr/bin/env bash
set -euo pipefail
PORT=18080
if curl -s -o /dev/null "http://localhost:$PORT/"; then echo "Port $PORT busy hai"; exit 1; fi
mkdir -p demo build
echo "<h1>Hello HTTP</h1>" > demo/index.html
nohup python3 -m http.server "$PORT" --directory demo >/dev/null 2>&1 &
echo $! > build/server.pid
sleep 1
