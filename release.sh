#!/usr/bin/env bash
set -euo pipefail

BUILD_TEMP="$(mktemp -d -t AssinadorDigital-build.XXXXXX)"
CERTS_PATH="$(realpath backend/certs)"

cleanup() {
  rm -rf "$BUILD_TEMP"
}
trap cleanup EXIT

python3 -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --windowed \
  --name AssinadorDigital \
  --paths backend \
  --hidden-import verifier \
  --collect-all PySide6 \
  --collect-all shiboken6 \
  --add-data "$CERTS_PATH:certs" \
  --distpath dist \
  --workpath "$BUILD_TEMP/work" \
  --specpath "$BUILD_TEMP" \
  desktop/local.py

EXE_PATH="$(realpath dist/AssinadorDigital)"
HASH="$(sha256sum "$EXE_PATH" | awk '{print $1}')"
echo "$HASH  AssinadorDigital" > dist/SHA256-linux.txt

echo "Build concluído e SHA-256 verificado: $HASH"
