#!/bin/bash
# Start the trainer in the background unless it already runs, then open it in the browser.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL=http://127.0.0.1:8642
if ! curl -s -o /dev/null "$URL"; then
    for PY in "$HOME/.pyenv/shims/python3" /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
        [ -x "$PY" ] && "$PY" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null && break
    done
    cd "$ROOT" && nohup "$PY" -m trainer > progress/server.log 2>&1 &
    for _ in {1..50}; do
        curl -s -o /dev/null "$URL" && break
        sleep 0.1
    done
fi
open -a Firefox "$URL" 2>/dev/null || open "$URL"
