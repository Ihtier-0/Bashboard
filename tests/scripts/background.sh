#!/usr/bin/env bash
# Category 3: long-running. Runs until stopped externally (Stop button).
echo "Background loop started. Press Stop to terminate."
trap 'echo "Caught signal, exiting cleanly."; exit 0' TERM INT

i=1
while true; do
    echo "tick $i at $(date +%H:%M:%S)"
    i=$((i + 1))
    sleep 2
done
