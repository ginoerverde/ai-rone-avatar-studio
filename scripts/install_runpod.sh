#!/usr/bin/env bash
set -Eeuo pipefail

# One-time install on a CUDA RunPod/Vast instance. The persistent volume must
# be mounted at /workspace so a stopped compute pod does not lose the models.
# Run this only after `nvidia-smi` works: failing early is cheaper than a
# partially installed GPU stack on a broken host.
ROOT=/workspace
APP="$ROOT/ai-rone-avatar-studio"
MODELS="$ROOT/ai-rone-models"
REPOS="$ROOT/ai-rone-repos"
VENV="$ROOT/venvs/avatar-studio"

# Do not race the Vast base-image bootstrap.  On some hosts its initial apt
# transaction can be slow; our installer only invokes apt when FFmpeg or git
# is actually absent and bounds the wait so the job fails visibly instead of
# leaving the instance apparently "Connecting" forever.
export DEBIAN_FRONTEND=noninteractive
APT_TIMEOUT="${AI_RONE_APT_TIMEOUT:-300}"
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: NVIDIA driver is not visible. Choose another Vast host before installing." >&2
  exit 20
fi
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
  timeout "$APT_TIMEOUT" apt-get update
  timeout "$APT_TIMEOUT" apt-get install -y --no-install-recommends \
    ffmpeg git sox libsox-dev libgl1 libglib2.0-0
fi
mkdir -p "$MODELS" "$REPOS" "$ROOT/ai-rone-data" "$ROOT/venvs"

if [ ! -d "$REPOS/MuseTalk/.git" ]; then git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git "$REPOS/MuseTalk"; fi
if [ ! -d "$REPOS/chatterbox/.git" ]; then git clone --depth 1 https://github.com/resemble-ai/chatterbox.git "$REPOS/chatterbox"; fi

PYTHON_BIN="${AI_RONE_PYTHON:-python3}"
"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required")
print("Using Python", sys.version)
PY
"$PYTHON_BIN" -m venv "$VENV"
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
python - <<'PY'
import shutil, torch
assert shutil.which("ffmpeg"), "FFmpeg missing after install"
assert torch.cuda.is_available(), "PyTorch cannot use CUDA"
print("CUDA ready:", torch.cuda.get_device_name(0))
PY
test -f "$REPOS/MuseTalk/models/musetalkV15/unet.pth"
touch "$APP/.installed"
echo "Installed and verified. Start the web UI with: $APP/scripts/start.sh"
