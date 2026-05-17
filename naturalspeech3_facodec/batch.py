# -*- coding: utf-8 -*-
"""
batch_voice_conversion.py
使用 FACodec V2 将 source_dir 中所有 .wav 语音转换为目标说话人音色。
- 自动对齐音频长度到 200 的倍数（FACodec 要求）
- 自动跳过已存在的输出文件
"""

import os
import torch
import librosa
import soundfile as sf
from ns3_codec import FACodecEncoderV2, FACodecDecoderV2
from huggingface_hub import hf_hub_download

# ================= 配置 =================
SOURCE_DIR = "D:\Pycharm\PyCharm_pro2023.3.4\creater\pythonProject2\zsctsd\master\TransformerTTS\outputswavs\wavs"               # 源语音文件夹
TEMPLATE_WAV = "audio/1.wav"              # 目标说话人参考语音
OUTPUT_DIR = "outputs/converted"          # 输出文件夹
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
HOP_SIZE = 200                            # FACodec 的 hop size (samples)
SAMPLE_RATE = 16000
# =========================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- 模型加载 ----------
print("加载 FACodec V2 模型...")
fa_encoder_v2 = FACodecEncoderV2(
    ngf=32, up_ratios=[2, 4, 5, 5], out_channels=256,
)
fa_decoder_v2 = FACodecDecoderV2(
    in_channels=256, upsample_initial_channel=1024, ngf=32,
    up_ratios=[5, 5, 4, 2],
    vq_num_q_c=2, vq_num_q_p=1, vq_num_q_r=3,
    vq_dim=256, codebook_dim=8,
    codebook_size_prosody=10, codebook_size_content=10, codebook_size_residual=10,
    use_gr_x_timbre=True, use_gr_residual_f0=True, use_gr_residual_phone=True,
)

# 下载权重（如网络问题请手动下载）
try:
    encoder_v2_ckpt = hf_hub_download(
        repo_id="amphion/naturalspeech3_facodec", filename="ns3_facodec_encoder_v2.bin"
    )
    decoder_v2_ckpt = hf_hub_download(
        repo_id="amphion/naturalspeech3_facodec", filename="ns3_facodec_decoder_v2.bin"
    )
except Exception as e:
    print(f"自动下载失败：{e}")
    print("请手动下载并修改路径")
    exit(1)

fa_encoder_v2.load_state_dict(torch.load(encoder_v2_ckpt, map_location=DEVICE))
fa_decoder_v2.load_state_dict(torch.load(decoder_v2_ckpt, map_location=DEVICE))
fa_encoder_v2.eval().to(DEVICE)
fa_decoder_v2.eval().to(DEVICE)

# ---------- 音频加载函数（确保长度对齐） ----------
def load_audio_aligned(path: str):
    """加载音频并填充/截断至 hop_size 的整数倍"""
    wav, _ = librosa.load(path, sr=SAMPLE_RATE)
    length = len(wav)
    if length % HOP_SIZE != 0:
        # 向上填充到 hop_size 的整数倍（用静音填充）
        pad_len = HOP_SIZE - (length % HOP_SIZE)
        wav = torch.nn.functional.pad(
            torch.tensor(wav), (0, pad_len), mode='constant', value=0
        ).numpy()
    wav_tensor = torch.tensor(wav, dtype=torch.float32, device=DEVICE).unsqueeze(0).unsqueeze(0)
    return wav_tensor

# ---------- 提取目标说话人特征 ----------
print("提取目标说话人特征...")
template_wav = load_audio_aligned(TEMPLATE_WAV)
with torch.no_grad():
    enc_template = fa_encoder_v2(template_wav)
    prosody_template = fa_encoder_v2.get_prosody_feature(template_wav)
    _, _, _, _, spk_embs_template = fa_decoder_v2(
        enc_template, prosody_template, eval_vq=False, vq=True
    )

# ---------- 批量转换 ----------
wav_files = sorted([f for f in os.listdir(SOURCE_DIR) if f.endswith('.wav')])
print(f"找到 {len(wav_files)} 个源语音文件，开始转换...")

for idx, fname in enumerate(wav_files):
    out_path = os.path.join(OUTPUT_DIR, fname)
    if os.path.exists(out_path):
        print(f"[{idx+1:03d}/{len(wav_files):03d}] {fname} 已存在，跳过")
        continue

    src_path = os.path.join(SOURCE_DIR, fname)
    src_wav = load_audio_aligned(src_path)

    with torch.no_grad():
        # 提取源语音特征
        enc_src = fa_encoder_v2(src_wav)
        prosody_src = fa_encoder_v2.get_prosody_feature(src_wav)
        # 量化
        _, vq_id_src, _, _, _ = fa_decoder_v2(
            enc_src, prosody_src, eval_vq=False, vq=True
        )
        # 用目标音色重建
        vq_post_emb = fa_decoder_v2.vq2emb(vq_id_src, use_residual=False)
        recon_wav = fa_decoder_v2.inference(vq_post_emb, spk_embs_template)

    sf.write(out_path, recon_wav[0][0].cpu().numpy(), SAMPLE_RATE)
    print(f"[{idx+1:03d}/{len(wav_files):03d}] {fname} 转换完成 → {out_path}")

print("全部转换完成！")