#!/bin/bash

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Create missing $ENV_FILE file before starting this script!"
    exit
fi

KEYS_DIR="keys"
PRIVATE_KEY="$KEYS_DIR/private_key.pem"
PUBLIC_KEY="$KEYS_DIR/public_key.pem"

# 2. Check if keys already exist to prevent overwriting them on container/server restarts
if [ -f "$PRIVATE_KEY" ] && [ -f "$PUBLIC_KEY" ]; then
    rm $PRIVATE_KEY
    rm $PUBLIC_KEY
fi

echo "[+] Initializing cryptographic key pair setup..."

mkdir -p "$KEYS_DIR"

openssl genpkey -algorithm RSA -out "$PRIVATE_KEY" -pkeyopt rsa_keygen_bits:4096 2> /dev/null
openssl rsa -pubout -in "$PRIVATE_KEY" -out "$PUBLIC_KEY" 2> /dev/null

chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"

echo "[+] Cryptographic key pair generated securely inside '$KEYS_DIR/'."
