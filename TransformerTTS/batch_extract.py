# -*- coding: utf-8 -*-
"""
batch_synthesize.py
使用 TransformerTTS 预训练模型逐条合成 stego_texts_100.txt 中的文本
输出 sample_000.wav ~ sample_099.wav 到 outputs/wavs/
依赖: pip install -r requirements.txt && sudo apt-get install espeak
"""

import os
import numpy as np
import soundfile as sf
from data.audio import Audio
from model.factory import tts_ljspeech

# ---------- 配置 ----------
TEXT_FILE   = "stego_100.txt"   # 每行一个待合成句子
OUTPUT_DIR  = "outputswavs/wavs"
# --------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. 加载预训练模型 (与官方 readme 完全一致)
print("加载 TransformerTTS 预训练模型 ...")
model = tts_ljspeech()                            # 官方 API
audio = Audio.from_config(model.config)           # 官方 API

# 2. 读取待合成文本
with open(TEXT_FILE, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"共 {len(lines)} 条文本，开始合成 ...")

# 3. 逐条合成并保存
for idx, text in enumerate(lines):
    # 官方 API 调用: model.predict() 返回 {'mel': Tensor}
    out = model.predict(text)                     # 官方 API

    # 官方 API 调用: 将 mel 谱图重建为波形
    wav = audio.reconstruct_waveform(out['mel'].numpy().T)  # 官方 API
    wav = wav.astype(np.float32)

    fname = os.path.join(OUTPUT_DIR, f"sample_{idx:03d}.wav")
    sf.write(fname, wav, model.config['sampling_rate'])
    print(f"[{idx+1:03d}/{len(lines):03d}] {fname}")

print("全部完成。")