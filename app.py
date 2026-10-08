"""Simple one-click UI for the economical MuseTalk avatar pipeline."""
from __future__ import annotations
import threading
from pathlib import Path
import gradio as gr
from studio import Studio, ROOT

s=Studio()
CSS=""".gradio-container{background:#080b12;color:#eef3ff}.main-title{font-size:32px;font-weight:800;letter-spacing:.5px}.subtitle{color:#9eb0ca}.primary{background:#3c76ff!important;border:0!important}footer{display:none!important}"""
def choices(items,default): return gr.Dropdown(choices=items,value=default if default in items else (items[0] if items else None))
def save_avatar(name,ref,prompt,quad): return s.save_avatar(name,ref,prompt,quad)
def save_voice(name,ref,engine,controls): return s.save_voice(name,ref,engine,{"controls":controls})
def voice_preview(reference,text): return s.voice_test(reference,text,"chatterbox_v3")
def generate(project,avatar,voice,script,screen,prompt):
    j=s.create(project,avatar,voice,script,screen,prompt); threading.Thread(target=s.run,args=(j.id,),daemon=True).start(); return j.id, f"Queued {j.id}: cloned voice → MuseTalk lip-sync → FFmpeg master → QC."
def job_status(job_id):
    if not job_id:return "No job selected.",None,None
    try:
        j=s.get(job_id); text=f"{j.state.upper()} — {j.stage} — {j.progress:.0%}"+(f"\nError: {j.error}" if j.error else ""); return text, j.output if j.output else None, str(s.log(j))
    except Exception as e:return str(e),None,None
def refresh(): return gr.Dropdown(choices=[p.parent.name for p in (ROOT/'jobs').glob('*/job.json')])
with gr.Blocks(css=CSS,title="AI-RONE Academy | Avatar Studio") as demo:
    gr.HTML("<div class='main-title'>AI-RONE Academy — Avatar Studio</div><div class='subtitle'>One script. One final 1080p lesson.</div>")
    with gr.Tabs():
      with gr.Tab("Generate Lesson"):
        with gr.Row(): project=gr.Textbox(label="Project name",value="LEZIONE_01"); avatar=choices(s.avatars(),"LUCA_ACCADEMIA"); voice=choices(s.voices(),"LUCA_IT_ACCADEMIA")
        script=gr.Textbox(label="Full lesson script",lines=18,placeholder="Paste the entire Italian lesson here.")
        with gr.Row(): screen=gr.File(label="Screen Content (optional: MP4, MOV, PNG, JPEG)",file_types=["video","image"]); prompt=gr.Textbox(label="Visual Prompt",lines=4,placeholder="Taken from Avatar Profile by default.")
        gr.Markdown("Output is locked to **1920×1080 · 25 fps · H.264/AAC**. Your source-avatar video is looped internally to cover the full audio; no clip assembly is required.")
        go=gr.Button("GENERATE LESSON",variant="primary",elem_classes="primary"); current=gr.Textbox(label="Job ID"); notice=gr.Textbox(label="Pipeline")
        go.click(generate,[project,avatar,voice,script,screen,prompt],[current,notice])
      with gr.Tab("Avatar Setup"):
        an=gr.Textbox(label="Avatar Profile",value="LUCA_ACCADEMIA"); ref=gr.File(label="Source Avatar Video (MP4 preferred)",file_types=["video"]); ap=gr.Textbox(label="Locked studio prompt",lines=6,value="Professional Italian instructor, full body, standing beside a large clean display, calm natural gestures, stable studio lighting, medium-wide camera, presenter never covers display."); quad=gr.Textbox(label="Monitor preset / notes",value="Add the screen separately in the edit for this first economical version."); gr.Button("Save Avatar Profile").click(save_avatar,[an,ref,ap,quad],gr.Textbox(label="Avatar status"))
      with gr.Tab("Voice Lab"):
        vn=gr.Textbox(label="Voice Profile",value="LUCA_IT_ACCADEMIA"); vr=gr.File(label="Reference WAV",file_types=["audio"]); vt=gr.Textbox(label="Italian test text",lines=5,value="Benvenuto. In questa lezione vedremo come trasformare un'idea in una scena con l'intelligenza artificiale."); gr.Button("Generate voice preview").click(voice_preview,[vr,vt],gr.Audio(label="Chatterbox Multilingual V3",type="filepath")); ve=gr.State("chatterbox_v3"); vc=gr.Textbox(label="Voice notes",lines=3,value="Italian; preserve natural rhythm and pronunciation of technical terms."); gr.Button("Save Voice Profile").click(save_voice,[vn,vr,ve,vc],gr.Textbox(label="Voice status")); gr.Markdown("The permanent profile keeps the reference audio and the selected Chatterbox configuration.")
      with gr.Tab("Jobs"):
        with gr.Row(): jid=gr.Textbox(label="Job ID",value=""); gr.Button("Refresh jobs").click(refresh,None,jid)
        gr.Button("Check status").click(job_status,jid,[gr.Textbox(label="Status"),gr.File(label="Final MP4"),gr.File(label="Log")])
      with gr.Tab("Advanced"):
        gr.Markdown("Defaults use official MuseTalk 1.5 in FP16, Chatterbox Multilingual V3 and FFmpeg. Advanced overrides are deliberately excluded from the main generation screen.")
demo.queue(default_concurrency_limit=1).launch(server_name="0.0.0.0",server_port=7860,show_error=True)
