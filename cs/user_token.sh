#!/bin/bash

if [ "$FIZIT_ENV" = "dev" ]; then
    OUTPUT="devnet_user_session.json"
    PURPOSE="User_DEV"
elif [ "$FIZIT_ENV" = "test" ]; then
    OUTPUT="testnet_user_session.json"
    PURPOSE="User_TEST"
elif [ "$FIZIT_ENV" = "main" ]; then
    OUTPUT="mainnet_user_session.json"
    PURPOSE="User_MAIN"
else
    echo "Error: FIZIT_ENV is not set to a valid value (dev, test, or main)."
    exit 1
fi

./cs token create --purpose $PURPOSE --user --scope 'manage:*' --output json --session-lifetime 31536000 --auth-lifetime 31536000 --refresh-lifetime 1 --save $OUTPUT --force-lifetimes
