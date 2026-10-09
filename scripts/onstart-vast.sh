#!/usr/bin/env bash
# Vast.ai on-start command. Return immediately so Vast can bring up Jupyter;
# installation and the Avatar Studio UI continue in the background.
set -Eeuo pipefail

ROOT=/workspace
APP="$ROOT/ai-rone-avatar-studio"
DATA="$ROOT/ai-rone-data"
LOG="$DATA/onstart.log"

mkdir -p "$DATA"

(
  export DEBIAN_FRONTEND=noninteractive

  if [ ! -d "$APP/.git" ]; then
    git clone --depth 1 https://github.com/ginoerverde/ai-rone-avatar-studio.git "$APP"
  else
    git -C "$APP" pull --ff-only
  fi

  if [ ! -f "$APP/.installed" ]; then
    bash "$APP/scripts/install_runpod.sh"
  fi

  nohup bash "$APP/scripts/start.sh" >"$DATA/app.log" 2>&1 &
) >"$LOG" 2>&1 &

exit 0
