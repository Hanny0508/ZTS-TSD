import time
import os
import sys
import tracemalloc
import torch
import argparse
import warnings
warnings.filterwarnings("ignore")
import sys
sys.path.insert(0, r"D:\Pycharm\PyCharm_pro2023.3.4\creater\pythonProject2\zsctsd\master\naturalspeech3_facodec")

# ================== 工具函数 ==================
def count_parameters(model):
    return sum(p.numel() for p in model.parameters())

def format_size(num_params):
    if num_params >= 1e9:
        return f"{num_params / 1e9:.2f}B"
    elif num_params >= 1e6:
        return f"{num_params / 1e6:.2f}M"
    else:
        return f"{num_params / 1e3:.2f}K"

def measure_dual_channel_overhead(data_id="test-uuid-1234"):
    import sqlite3, hmac, hashlib
    t0 = time.time()
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id TEXT, ts TEXT, status TEXT)")
    conn.execute("INSERT INTO test VALUES (?, datetime('now'), 'pending')", (data_id,))
    conn.commit()
    for _ in range(3):
        conn.execute("SELECT status FROM test WHERE id=?", (data_id,)).fetchone()
    sig = hmac.new(b"test_key", data_id.encode(), hashlib.sha256).hexdigest()
    conn.execute("UPDATE test SET status='received' WHERE id=?", (data_id,))
    conn.commit()
    conn.close()
    t1 = time.time()
    return (t1 - t0) * 1000

# ================== 主程序 ==================
def main():
    parser = argparse.ArgumentParser(description="Compute system overhead")
    parser.add_argument("--skip-zts", action="store_true")
    parser.add_argument("--skip-tts", action="store_true")
    parser.add_argument("--skip-dual", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("System Overhead Analysis")
    print("=" * 60)
    results = {}

    # ------------------- 1. ZTS 模块 (DistilGPT-2) -------------------
    if not args.skip_zts:
        print("\n[1/3] Zero-Shot Text Steganography (ZTS)")
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            model_name = "distilgpt2"
            print(f"  Loading {model_name}...")
            t0 = time.time()
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if torch.cuda.is_available():
                model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
            else:
                model = AutoModelForCausalLM.from_pretrained(model_name)
            model.eval()
            t1 = time.time()
            params = count_parameters(model)
            print(f"    Load time: {t1 - t0:.2f}s")
            print(f"    Parameters: {format_size(params)}")

            prompt = "This is a test sentence for measuring steganography generation."
            inputs = tokenizer(prompt, return_tensors="pt")
            device = next(model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            tracemalloc.start()
            times = []
            for i in range(10):
                torch.cuda.synchronize() if torch.cuda.is_available() else None
                t_start = time.time()
                with torch.no_grad():
                    _ = model(**inputs)
                torch.cuda.synchronize() if torch.cuda.is_available() else None
                t_end = time.time()
                times.append(t_end - t_start)
                if i == 0:
                    _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            avg_time = sum(times) / len(times)
            peak_mem = peak / 1024 / 1024

            print(f"    Avg inference time: {avg_time*1000:.1f} ms")
            print(f"    Peak memory: {peak_mem:.1f} MB")
            results["ZTS"] = {
                "model": "DistilGPT-2",
                "load_time_s": round(t1 - t0, 2),
                "params": format_size(params),
                "inf_time_ms": round(avg_time * 1000, 1),
                "peak_mem_MB": round(peak_mem, 1)
            }
        except Exception as e:
            print(f"  ZTS measurement failed: {e}")
            results["ZTS"] = {"error": str(e)}

    # ------------------- 2. TTS 模块 (espeak + FACodec) -------------------
    # ------------------- 2. TTS 模块 (FACodec decoder) -------------------
    if not args.skip_tts:
        print("\n[2/3] TTS Module (FACodec decoder)")
        try:
            print("  Loading FACodec V2 decoder...")
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "TransformerTTS"))
            from ns3_codec import FACodecDecoderV2
            from huggingface_hub import hf_hub_download

            fa_decoder = FACodecDecoderV2(
                in_channels=256, upsample_initial_channel=1024, ngf=32,
                up_ratios=[5, 5, 4, 2], vq_num_q_c=2, vq_num_q_p=1, vq_num_q_r=3,
                vq_dim=256, codebook_dim=8, codebook_size_prosody=10,
                codebook_size_content=10, codebook_size_residual=10,
                use_gr_x_timbre=True, use_gr_residual_f0=True,
                use_gr_residual_phone=True,
            )
            decoder_ckpt = hf_hub_download(
                repo_id="amphion/naturalspeech3_facodec",
                filename="ns3_facodec_decoder_v2.bin"
            )
            fa_decoder.load_state_dict(torch.load(decoder_ckpt, map_location="cpu"))
            fa_decoder.eval()
            decoder_params = sum(p.numel() for p in fa_decoder.parameters())
            print(f"    FACodec decoder params: {decoder_params / 1e6:.2f}M")

            # 修复：模拟量化编码 vq_post_emb，形状 [1, 256, T]
            # FACodec.inference 期望 vq_post_emb 形状为 [B, 256, T]
            T = 100  # 时长帧数
            dummy_vq = torch.randn(1, 256, T)
            dummy_spk = torch.randn(1, 256)

            tracemalloc.start()
            t0 = time.time()
            with torch.no_grad():
                recon = fa_decoder.inference(dummy_vq, dummy_spk)
            t1 = time.time()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            facodec_time = (t1 - t0) * 1000
            peak_mem = peak / 1024 / 1024
            print(f"    FACodec inference time: {facodec_time:.1f} ms")
            print(f"    Peak memory: {peak_mem:.1f} MB")

            results["TTS"] = {
                "facodec_params": f"{decoder_params / 1e6:.2f}M",
                "inf_time_ms": round(facodec_time, 1),
                "peak_mem_MB": round(peak_mem, 1)
            }
        except Exception as e:
            print(f"  TTS measurement failed: {e}")
            results["TTS"] = {"error": str(e)}


    # ------------------- 3. 双信道协议开销 -------------------
    if not args.skip_dual:
        print("\n[3/3] Dual-Channel Protocol Overhead")
        sync_time = measure_dual_channel_overhead()
        print(f"  Dual-channel sync overhead: {sync_time:.2f} ms")
        results["dual_channel"] = {"sync_overhead_ms": round(sync_time, 2)}

    # ================== 汇总 ==================
    print("\n" + "=" * 60)
    print("Summary of System Overhead")
    print("=" * 60)
    for module, data in results.items():
        print(f"\n{module}:")
        for key, val in data.items():
            print(f"  {key}: {val}")

    with open("overhead_results.txt", "w") as f:
        f.write("System Overhead Analysis Results\n")
        f.write("=" * 40 + "\n")
        for module, data in results.items():
            f.write(f"\n{module}:\n")
            for key, val in data.items():
                f.write(f"  {key}: {val}\n")

if __name__ == "__main__":
    main()