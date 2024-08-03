#!/bin/bash

# Read process IDs from the file and kill them
if [ -f pids.txt ]; then
    while read -r pid; do
        kill $pid
    done < pids.txt

    rm pids.txt
    echo "All processes stopped."
else
    echo "No processes to stop."
fi