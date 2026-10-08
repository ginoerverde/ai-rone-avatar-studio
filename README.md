# AI-RONE Academy — Avatar Studio

Economical production interface using the official MuseTalk 1.5 repository, official Chatterbox Multilingual V3 and FFmpeg. It provides one-click lesson jobs: script → cloned Italian voice → MuseTalk lip-sync on the saved avatar video → validated 1080p MP4.

## Persistent pod layout

Mount the persistent volume at `/workspace`. The installer creates `/workspace/ai-rone-avatar-studio`, `/workspace/ai-rone-models` and `/workspace/ai-rone-data`.

Start the UI with `./scripts/start.sh` and expose port `7860`.

## First acceptance run

1. In Avatar Setup, upload an approved 25 fps or longer LUCA studio video.
2. In Voice Lab, generate a Chatterbox preview from the Italian reference and save it as `LUCA_IT_ACCADEMIA`.
3. In Generate Lesson, enter a 60-second script and optionally upload a screen asset.
4. Record the resulting metrics before moving to 10 minutes.
