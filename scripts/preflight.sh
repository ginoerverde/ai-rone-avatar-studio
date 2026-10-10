#!/usr/bin/env bash
# Read-only verification before spending time downloading models.
set -Eeuo pipefail

echo '=== GPU ==='
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo '=== disk ==='
df -h /workspace
echo '=== network tools ==='
command -v git
command -v ffmpeg
echo '=== Python ==='
python3 --version
echo '=== workspace ==='
mkdir -p /workspace/ai-rone-data
test -w /workspace/ai-rone-data
echo 'PRECHECK_OK'
