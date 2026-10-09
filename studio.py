"""One-click Chatterbox → MuseTalk 1.5 → FFmpeg lesson pipeline."""
from __future__ import annotations
import json, os, shutil, subprocess, time, uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(os.getenv("AI_RONE_DATA", "/workspace/ai-rone-data"))
MUSE = Path(os.getenv("MUSE_TALK_REPO", "/workspace/ai-rone-repos/MuseTalk"))
CHATTERBOX = Path(os.getenv("CHATTERBOX_REPO", "/workspace/ai-rone-repos/chatterbox"))
FPS = 25
for part in ("profiles/avatars", "profiles/voices", "jobs", "outputs", "benchmarks"):
    (ROOT / part).mkdir(parents=True, exist_ok=True)

def _json(p: Path, default: Any = None): return json.loads(p.read_text()) if p.exists() else default
def _write(p: Path, value: Any): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(value, ensure_ascii=False, indent=2))
def _run(cmd: list[str], log: Path, cwd: Path | None = None):
    with log.open("a") as out:
        out.write("$ " + " ".join(map(str, cmd)) + "\n"); out.flush()
        if subprocess.run(cmd, cwd=cwd, stdout=out, stderr=subprocess.STDOUT).returncode:
            raise RuntimeError(f"Command failed; see {log}")
def _probe(p: Path): return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)], text=True))
def _duration(p: Path): return float(_probe(p)["format"]["duration"])
def _safe(name: str): return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_") or "LESSON"
def split_script(text: str, limit: int = 900):
    words = text.replace("\n", " ").split(); chunks=[]; current=[]; n=0
    for w in words:
        if current and n + len(w) + 1 > limit: chunks.append(" ".join(current)); current=[]; n=0
        current.append(w); n += len(w) + 1
        if w.endswith((".", "!", "?")) and n > 430: chunks.append(" ".join(current)); current=[]; n=0
    if current: chunks.append(" ".join(current))
    return chunks

@dataclass
class Job:
    id: str; project: str; avatar: str; voice: str; script: str; screen: str | None; visual_prompt: str
    state: str="queued"; stage: str="queued"; progress: float=0.; error: str | None=None; output: str | None=None; started_at: float | None=None; updated_at: float | None=None

class Studio:
    def avatar_path(self, n): return ROOT / "profiles/avatars" / f"{n}.json"
    def voice_path(self, n): return ROOT / "profiles/voices" / f"{n}.json"
    def job_path(self, n): return ROOT / "jobs" / n / "job.json"
    def avatars(self): return [p.stem for p in (ROOT / "profiles/avatars").glob("*.json")]
    def voices(self): return [p.stem for p in (ROOT / "profiles/voices").glob("*.json")]
    def log(self, j): return self.job_path(j.id).parent / "run.log"
    def put(self, j): j.updated_at=time.time(); _write(self.job_path(j.id), asdict(j))
    def get(self, n): return Job(**_json(self.job_path(n)))
    def save_avatar(self, name, reference, prompt, quad):
        if not name or not reference: raise ValueError("Profile name and source avatar video are required.")
        target=self.avatar_path(name).parent / f"{name}{Path(reference).suffix}"; shutil.copy2(reference, target)
        _write(self.avatar_path(name), {"name":name,"reference":str(target),"prompt":prompt,"monitor_quad":quad})
        return f"Saved avatar profile {name}."
    def save_voice(self, name, reference, engine, controls):
        if not name or not reference: raise ValueError("Profile name and reference WAV are required.")
        target=self.voice_path(name).parent / f"{name}{Path(reference).suffix}"; shutil.copy2(reference, target)
        _write(self.voice_path(name), {"name":name,"reference":str(target),"engine":engine,"controls":controls})
        return f"Saved voice profile {name}."
    def _tts(self, voice, text, dst, log):
        parts=[]
        for i, chunk in enumerate(split_script(text)):
            part=dst.parent / f"tts_{i:03}.wav"; parts.append(part)
            code=("from chatterbox.mtl_tts import ChatterboxMultilingualTTS as M; import torchaudio; "
                  "m=M.from_pretrained(device='cuda'); a=m.generate(" + repr(chunk) + ",language_id='it',audio_prompt_path=" + repr(str(voice['reference'])) + "); torchaudio.save(" + repr(str(part)) + ",a,m.sr)")
            _run(["python", "-c", code], log, CHATTERBOX)
        manifest=dst.parent / "audio_concat.txt"; manifest.write_text("".join(f"file '{p}'\n" for p in parts))
        _run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(manifest),"-af","loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000","-ar","48000","-ac","1",str(dst)],log)
    def voice_test(self, reference, text, engine):
        if engine != "chatterbox_v3": raise ValueError("Only Chatterbox Multilingual V3 is installed in this economical build.")
        work=ROOT / "jobs" / f"voice_lab_{uuid.uuid4().hex[:8]}"; work.mkdir(parents=True)
        out=work / "preview.wav"; self._tts({"reference":reference,"engine":engine},text,out,work / "voice_lab.log"); return str(out)
    def create(self, project, avatar, voice, script, screen, prompt):
        if not project.strip() or not script.strip(): raise ValueError("Project name and full script are required.")
        if not self.avatar_path(avatar).exists() or not self.voice_path(voice).exists(): raise ValueError("Select saved avatar and voice profiles.")
        j=Job(uuid.uuid4().hex[:12],project.strip(),avatar,voice,script,screen,prompt); self.put(j); return j
    def _prepare_source(self, source, audio, work, log):
        target=work / "avatar_25fps.mp4"; seconds=_duration(audio)
        _run(["ffmpeg","-y","-stream_loop","-1","-i",str(source),"-t",f"{seconds:.3f}","-vf",f"fps={FPS},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2","-an","-c:v","libx264","-crf","18","-pix_fmt","yuv420p",str(target)],log)
        return target
    def _musetalk(self, source, audio, work, log):
        config=work / "musetalk.yaml"; result=work / "musetalk"; result.mkdir()
        config.write_text(yaml.safe_dump({"lesson": {"video_path":str(source),"audio_path":str(audio),"result_name":"lipsync.mp4"}}))
        _run(["python","-m","scripts.inference","--inference_config",str(config),"--result_dir",str(result),"--unet_model_path","models/musetalkV15/unet.pth","--unet_config","models/musetalkV15/musetalk.json","--version","v15","--fps",str(FPS),"--use_float16","--saved_coord"],log,MUSE)
        output=result / "v15" / "lipsync.mp4"
        if not output.exists(): raise RuntimeError("MuseTalk did not create lipsync.mp4.")
        return output
    def _screen_filter(self, screen: str | None, duration: float, work: Path, log: Path):
        """Create a full-HD screen layer without sending readable content to AI."""
        layer = work / "screen_layer.mp4"
        if not screen:
            _run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x151b28:s=1920x1080:r=25",
                  "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(layer)], log)
        elif Path(screen).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            _run(["ffmpeg", "-y", "-loop", "1", "-i", screen, "-t", f"{duration:.3f}",
                  "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                  "-r", "25", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(layer)], log)
        else:
            _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", screen, "-t", f"{duration:.3f}",
                  "-vf", "fps=25,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                  "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(layer)], log)
        return layer
    def run(self, job_id):
        j=self.get(job_id); work=self.job_path(j.id).parent; log=self.log(j); j.state="running"; j.started_at=time.time(); self.put(j)
        try:
            voice=_json(self.voice_path(j.voice)); avatar=_json(self.avatar_path(j.avatar))
            j.stage="Chatterbox: cloned Italian master audio"; j.progress=.08; self.put(j)
            audio=work / "master_48k.wav"; self._tts(voice,j.script,audio,log)
            j.stage="Preparing avatar source at 25 fps"; j.progress=.28; self.put(j)
            source=self._prepare_source(avatar["reference"],audio,work,log)
            j.stage="MuseTalk 1.5 lip-sync"; j.progress=.42; self.put(j)
            raw=self._musetalk(source,audio,work,log)
            # MuseTalk's result can be video-only.  The master audio is always
            # remuxed explicitly, so final A/V duration is deterministic.
            j.stage="Compositing display and master audio"; j.progress=.72; self.put(j)
            screen_layer=self._screen_filter(j.screen, _duration(audio), work, log)
            j.stage="Encoding final 1080p MP4"; j.progress=.88; self.put(j)
            final=ROOT / "outputs" / f"{_safe(j.project)}_1080p_FINAL.mp4"
            # First economical build: source-video layout keeps the presenter
            # on the left while a crisp, separately rendered display sits right.
            _run(["ffmpeg","-y","-i",str(raw),"-i",str(screen_layer),"-i",str(audio),
                  "-filter_complex","[0:v]fps=25,scale=960:1080:force_original_aspect_ratio=decrease,pad=960:1080:(ow-iw)/2:(oh-ih)/2[p];[1:v]scale=960:1080[s];[p][s]hstack=inputs=2[v]",
                  "-map","[v]","-map","2:a:0","-t",f"{_duration(audio):.3f}","-r",str(FPS),"-fps_mode","cfr",
                  "-c:v","libx264","-preset","slow","-crf","17","-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-ar","48000",str(final)],log)
            info=_probe(final); streams={s["codec_type"]:s for s in info["streams"]}; v=streams.get("video")
            if not final.exists() or not v or "audio" not in streams or int(v["width"]) != 1920 or int(v["height"]) != 1080 or abs(_duration(final)-_duration(audio)) > .20: raise RuntimeError("QC failed: output stream, dimensions or A/V sync is invalid.")
            j.state="completed"; j.stage="completed"; j.progress=1.; j.output=str(final); self.put(j)
        except Exception as e:
            j.state="failed"; j.stage="failed"; j.error=str(e); self.put(j)
        return j
