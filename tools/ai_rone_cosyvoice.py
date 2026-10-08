import argparse
import torchaudio
from cosyvoice.cli.cosyvoice import AutoModel
p=argparse.ArgumentParser(); p.add_argument('--model'); p.add_argument('--reference'); p.add_argument('--text'); p.add_argument('--output'); a=p.parse_args()
m=AutoModel(model_dir=a.model); r=next(m.inference_zero_shot(a.text,'',a.reference)); torchaudio.save(a.output,r['tts_speech'],m.sample_rate)
