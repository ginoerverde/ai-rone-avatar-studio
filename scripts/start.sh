#!/usr/bin/env bash
set -Eeuo pipefail
source /workspace/venvs/avatar-studio/bin/activate
export AI_RONE_DATA=/workspace/ai-rone-data
export MUSE_TALK_REPO=/workspace/ai-rone-repos/MuseTalk
export CHATTERBOX_REPO=/workspace/ai-rone-repos/chatterbox
export HF_HOME=/workspace/ai-rone-models/hf
export HF_HUB_CACHE=/workspace/ai-rone-models/hf/hub
cd /workspace/ai-rone-avatar-studio
python app.py
