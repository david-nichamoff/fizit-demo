#!/bin/bash

if [ "$FIZIT_ENV" = "dev" ]; then
    ROLE_ID="Role#678259b3-0363-4238-80a7-1f88951ae560"
    OUTPUT="devnet_role_session.json"
    PURPOSE="Role_DEV"
elif [ "$FIZIT_ENV" = "test" ]; then
    ROLE_ID="Role#1f73c3f6-93a0-4aa3-b083-f1c71a6d2448"
    OUTPUT="testnet_role_session.json"
    PURPOSE="Role_TEST"
elif [ "$FIZIT_ENV" = "main" ]; then
    ROLE_ID="<change me>"
    OUTPUT="mainnet_role_session.json"
    PURPOSE="Role_MAIN"
else
    echo "Error: FIZIT_ENV is not set to a valid value (dev, test, or main)."
    exit 1
fi

./cs token create --purpose $PURPOSE  --role-id $ROLE_ID --scope 'sign:*' --output json --session-lifetime 31536000 --auth-lifetime 31536000 --refresh-lifetime 1 --save $OUTPUT
