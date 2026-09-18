#!/usr/bin/env bash
[ -f build/server.pid ] && kill "$(cat build/server.pid)" 2>/dev/null; rm -f build/server.pid
