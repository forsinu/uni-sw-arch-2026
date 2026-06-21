#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

CERT_DIR="${FRONTEND_HTTPS_CERT_DIR:-$SCRIPT_DIR/certs}"
KEY_FILE="${FRONTEND_HTTPS_KEY_FILE:-$CERT_DIR/localhost.key}"
CERT_FILE="${FRONTEND_HTTPS_CERT_FILE:-$CERT_DIR/localhost.crt}"
DAYS="${FRONTEND_HTTPS_CERT_DAYS:-365}"
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --force)
      FORCE=true
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: ./deploy.sh [--force]" >&2
      exit 2
      ;;
  esac
done

if ! command -v openssl >/dev/null 2>&1; then
  echo "OpenSSL is required to generate a local HTTPS certificate." >&2
  exit 1
fi

mkdir -p "$CERT_DIR"

if [ -f "$KEY_FILE" ] && [ -f "$CERT_FILE" ] && [ "$FORCE" = false ]; then
  echo "Frontend HTTPS certificate already exists:"
  echo "  certificate: $CERT_FILE"
  echo "  private key: $KEY_FILE"
  echo
  echo "Use './deploy.sh --force' to regenerate it."
else
  openssl req \
    -x509 \
    -nodes \
    -days "$DAYS" \
    -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:frontend.localhost,DNS:app.docker.localhost,IP:127.0.0.1"

  chmod 600 "$KEY_FILE"
  chmod 644 "$CERT_FILE"

  echo "Generated frontend HTTPS certificate:"
  echo "  certificate: $CERT_FILE"
  echo "  private key: $KEY_FILE"
fi

echo
echo "Starting Angular frontend container over HTTPS..."
echo "URL: https://localhost:4200"
echo

cd "$SCRIPT_DIR"
docker compose up --build
