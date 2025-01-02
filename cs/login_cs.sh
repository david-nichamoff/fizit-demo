#!/bin/bash

if [ "$FIZIT_ENV" = "dev" ] || [ "$FIZIT_ENV" = "test" ]; then
    ./cs login david@fizit.biz --env gamma
elif [ "$FIZIT_ENV" = "main" ]; then
    ./cs login david@fizit.biz --env prod
else
    echo "Error: FIZIT_ENV is not set to a valid value (dev, test, or main)."
    exit 1
fi
