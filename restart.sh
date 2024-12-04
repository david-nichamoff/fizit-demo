#!/bin/bash

# Define the paths to the start and stop scripts
START_SCRIPT="start.sh"
STOP_SCRIPT="stop.sh"

# Check if stop.sh exists and is executable
if [ -x "$STOP_SCRIPT" ]; then
    echo "Stopping existing processes..."
    bash "$STOP_SCRIPT"
else
    echo "Error: $STOP_SCRIPT not found or not executable. Aborting."
    exit 1
fi

# Check if start.sh exists and is executable
if [ -x "$START_SCRIPT" ]; then
    echo "Starting processes..."
    bash "$START_SCRIPT"
else
    echo "Error: $START_SCRIPT not found or not executable. Aborting."
    exit 1
fi

echo "Restart complete."