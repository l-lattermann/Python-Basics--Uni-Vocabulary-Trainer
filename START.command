#!/bin/bash
# Start the trainer in this terminal and open it in the browser; closing the window stops it.
cd "$(dirname "$0")"
URL=http://127.0.0.1:8642
if curl -s -o /dev/null "$URL"; then
    open -a Firefox "$URL" 2>/dev/null || open "$URL"
    exit
fi
python3 -m trainer &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT HUP INT TERM
for _ in {1..50}; do
    curl -s -o /dev/null "$URL" && break
    sleep 0.1
done
open -a Firefox "$URL" 2>/dev/null || open "$URL"
wait $SERVER
