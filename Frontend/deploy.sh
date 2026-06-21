#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Angular frontend container behind Traefik HTTPS..."
echo "URL: https://app.docker.localhost"
echo

cd "$SCRIPT_DIR"
docker compose up --build
