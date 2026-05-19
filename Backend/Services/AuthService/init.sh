#!/bin/bash

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Create missing $ENV_FILE file before starting this script!"
    exit
fi

NEW_SECRET=$(openssl rand -hex 32)

if grep -q "^SECRET_KEY=" "$ENV_FILE"; then

    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" "$ENV_FILE"
    echo "🔄 SECRET_KEY successfully overwritten with a fresh token!"
else

    echo "SECRET_KEY=$NEW_SECRET" >> "$ENV_FILE"
    echo "✅ SECRET_KEY was missing. Added new secure token!"
fi
