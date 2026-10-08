#!/usr/bin/env bash
# Vast.ai on-start command: install once on the persistent volume and serve UI.
set -Eeuo pipefail

ROOT=/workspace
APP="$ROOT/ai-rone-avatar-studio"

if [ ! -d "$APP/.git" ]; then
  git clone --depth 1 https://github.com/ginoerverde/ai-rone-avatar-studio.git "$APP"
else
  git -C "$APP" pull --ff-only
fi

if [ ! -f "$APP/.installed" ]; then
  bash "$APP/scripts/install_runpod.sh"
fi

nohup bash "$APP/scripts/start.sh" >"$ROOT/ai-rone-data/app.log" 2>&1 &
