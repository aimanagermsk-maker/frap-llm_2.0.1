#!/usr/bin/env bash
# Локальная сборка и запуск (Linux / macOS / Git Bash на Windows).

set -euo pipefail

IMAGE_NAME=frap-llm-helper-img
CONTAINER_NAME=frap-llm-helper-app
APP_PORT=8000
APP_PROFILE="${APP_PROFILE:-sandbox}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true
docker image rm -f "$IMAGE_NAME" 2>/dev/null || true

docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"

# -v: yaml settings/server/{profile}.yaml с хоста перезаписывает и дополняет свойства конфига профиля из образа
docker run -d \
  -p "${APP_PORT}:${APP_PORT}" \
  --restart unless-stopped \
  --name "$CONTAINER_NAME" \
  -e "APP_PROFILE=${APP_PROFILE}" \
  -v "${SCRIPT_DIR}/settings/server:/app/settings/server:ro" \
  "$IMAGE_NAME"

echo "Started ${CONTAINER_NAME} with APP_PROFILE=${APP_PROFILE}"
echo "http://localhost:${APP_PORT}/hello"
echo "http://localhost:${APP_PORT}/docs"
