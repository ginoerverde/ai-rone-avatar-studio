#!/usr/bin/env bash
set -Eeuo pipefail

# One-time install on a CUDA RunPod/Vast instance. The persistent volume must
# be mounted at /workspace so a stopped compute pod does not lose the models.
ROOT=/workspace
APP="$ROOT/ai-rone-avatar-studio"
MODELS="$ROOT/ai-rone-models"
REPOS="$ROOT/ai-rone-repos"
VENV="$ROOT/venvs/avatar-studio"

apt-get update
apt-get install -y --no-install-recommends ffmpeg git sox libsox-dev libgl1 libglib2.0-0
rm -rf /var/lib/apt/lists/*
mkdir -p "$MODELS" "$REPOS" "$ROOT/ai-rone-data" "$ROOT/venvs"

if [ ! -d "$REPOS/MuseTalk/.git" ]; then git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git "$REPOS/MuseTalk"; fi
if [ ! -d "$REPOS/chatterbox/.git" ]; then git clone --depth 1 https://github.com/resemble-ai/chatterbox.git "$REPOS/chatterbox"; fi

python3 -m venv "$VENV"
source "$VENV/bin/activate"
pip install --upgrade pip wheel
# RTX 50-series (Blackwell) needs a current CUDA 12.8 PyTorch build.  The
# earlier cu118 package cannot execute CUDA kernels on the RTX 5090.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -r "$REPOS/MuseTalk/requirements.txt"
pip install --no-cache-dir -U openmim
mim install mmengine
mim install "mmcv==2.0.1"
mim install "mmdet==3.1.0"
mim install "mmpose==1.1.0"
pip install -e "$REPOS/chatterbox"
pip install -r "$APP/requirements-ui.txt"

export HF_HOME="$MODELS/hf"
export HF_HUB_CACHE="$MODELS/hf/hub"
bash "$REPOS/MuseTalk/download_weights.sh"
echo "Installed. Start the web UI with: $APP/scripts/start.sh"
