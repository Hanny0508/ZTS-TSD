# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
estimate_speech_duration_by_syllable.py
统计 100 条合成语音中每音节平均发音时长，
再对 16000 条 stego text 按音节数逐词累加估算时长，输出整体均值。
需要：pip install syllapy librosa
"""
import csv
import syllapy
import librosa
import numpy as np
import os

# ================= 配置 =================
FULL_CSV = "imdb_s2.csv"               # 全部 16000 条隐写文本
FULL_COL = "stegotext"

NUM_SAMPLES = 100
# 使用原始字符串（r''）或正斜杠避免转义问题
AUDIO_DIR = r"D:\Pycharm\PyCharm_pro2023.3.4\creater\pythonProject2\zsctsd\master\naturalspeech3_facodec\outputs\converted"
AUDIO_TEMPLATE = "sample_{:03d}.wav"
TEXT_FILE = "stego_100.txt"            # 对应文本，每行一条
# ========================================

def count_syllables(text: str) -> int:
    """统计一段文本的总音节数（按空格分词后逐词统计）"""
    words = text.strip().split()
    total = 0
    for w in words:
        clean = ''.join(c for c in w if c.isalpha())
        if clean:
            total += syllapy.count(clean)
    return total

# 1. 读取 100 条样本文本和音频，统计总音节数和总时长
with open(TEXT_FILE, "r", encoding="utf-8") as f:
    sample_texts = [line.strip() for line in f if line.strip()]

assert len(sample_texts) == NUM_SAMPLES, (
    f"文本文件应有 {NUM_SAMPLES} 行，实际 {len(sample_texts)} 行"
)

total_syllables = 0
total_duration = 0.0

for idx, text in enumerate(sample_texts):
    audio_path = os.path.join(AUDIO_DIR, AUDIO_TEMPLATE.format(idx))
    # librosa 0.10+ 使用 path 参数
    dur = librosa.get_duration(path=audio_path)
    syll = count_syllables(text)
    total_duration += dur
    total_syllables += syll

avg_sec_per_syllable = total_duration / total_syllables if total_syllables > 0 else 0.0
print(f"100 条样本总音节数: {total_syllables}")
print(f"100 条样本总时长: {total_duration:.2f} s")
print(f"每音节平均时长: {avg_sec_per_syllable:.3f} s")

# 2. 处理全部 16000 条文本，逐条估算时长
with open(FULL_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    full_texts = [row[FULL_COL] for row in reader if row[FULL_COL].strip()]

est_durations = []
for text in full_texts:
    syll = count_syllables(text)
    est_dur = syll * avg_sec_per_syllable
    est_durations.append(est_dur)

avg_duration = np.mean(est_durations)
std_duration = np.std(est_durations)

print(f"\n全部 {len(full_texts)} 条文本的估算结果：")
print(f"平均语音时长: {avg_duration:.2f} s (标准差 {std_duration:.2f} s)")
print(f"最短: {min(est_durations):.2f} s, 最长: {max(est_durations):.2f} s")
print(f"\n➜ 填入表格 Steganographic Speech 的值: {avg_duration:.1f} s")