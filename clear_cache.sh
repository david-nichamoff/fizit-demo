#!/bin/sh

# Define the Redis host and port
REDIS_HOST="localhost"
REDIS_PORT="6379"

# Log start message
echo "Clearing Redis cache on ${REDIS_HOST}:${REDIS_PORT}..."

# Flush all Redis keys
if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" FLUSHALL; then
    echo "Redis cache cleared successfully."
else
    echo "Failed to clear Redis cache."
fi