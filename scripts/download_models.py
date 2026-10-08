"""Compatibility check: the official MuseTalk script downloads all its weights."""
from pathlib import Path
repo = Path("/workspace/ai-rone-repos/MuseTalk")
if not (repo / "models" / "musetalkV15" / "unet.pth").exists():
    raise SystemExit("Run scripts/install_runpod.sh first; it downloads official MuseTalk 1.5 weights.")
print("MuseTalk weights already available.")
