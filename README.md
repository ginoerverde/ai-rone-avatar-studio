# AI-RONE Academy — Avatar Studio

Economical production interface using the official MuseTalk 1.5 repository,
official Chatterbox Multilingual V3 and FFmpeg. It provides one-click lesson
jobs: script → cloned Italian voice → MuseTalk lip-sync on the saved avatar
video → validated 1080p MP4.

## Persistent RunPod layout

Mount the persistent volume at `/workspace`.  The installer creates:

```
/workspace/ai-rone-avatar-studio/     application
/workspace/ai-rone-models/            checkpoints and Hugging Face cache
/workspace/ai-rone-data/              profiles, jobs, outputs and logs
```

The compute container can be stopped at any time: models, profiles and jobs are
kept on the volume. Start the UI with `./scripts/start.sh`. On Vast SSH
instances it listens on port `8080`: use the SSH command supplied by Vast (it
forwards that port), then open `http://localhost:8080` on the same computer.

## First acceptance run

1. In **Avatar Setup**, upload an approved 25 fps or longer LUCA studio video
   with the natural body movement you want to preserve. It is looped internally
   when a lesson is longer.
2. In **Voice Lab**, generate a Chatterbox preview from the same Italian
   reference, then save it as `LUCA_IT_ACCADEMIA`.
3. In **Generate Lesson**, enter a 60-second script and upload a screen asset.
4. Record the resulting metrics in `benchmarks/` before moving to 10 minutes.

Never judge the system from a successful encode alone: inspect identity, mouth,
hands, eyes, background stability, source-video loop joins and voice similarity.
