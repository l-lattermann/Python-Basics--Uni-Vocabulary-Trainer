#!/bin/bash
cd "$(dirname "$0")"
python3 -m trainer &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT HUP INT TERM
for _ in {1..50}; do
    curl -s -o /dev/null http://127.0.0.1:8642/ && break
    sleep 0.1
done
open -a Firefox http://127.0.0.1:8642 2>/dev/null || open http://127.0.0.1:8642
wait $SERVER
