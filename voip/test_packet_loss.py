import os
import sys
import time
import random
import threading
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from VoIP.config import DB_PATH, TIMEOUT, MAX_RETRIES
from VoIP.database import init_db, insert_pending, get_state, update_to_received
from VoIP.channel import send_audio_over_main
from VoIP.voip_utils import generate_data_id, current_timestamp, compute_hmac
from VoIP.receiver import Receiver


def run_single_trial(loss_rate, audio_path, trial_id):
    """测试单条消息在给定丢包率下的传输结果"""
    log = []
    init_db()
    data_id = generate_data_id()
    timestamp = current_timestamp()
    insert_pending(data_id, timestamp)

    log.append(f"  [Trial #{trial_id}] data_id={data_id}, loss_rate={loss_rate}")

    # 启动接收方
    receiver = Receiver(save_dir="./received_audio")
    recv_thread = threading.Thread(target=receiver.start, daemon=True)
    recv_thread.start()
    time.sleep(0.5)

    success = False
    attempts = 0

    while attempts < MAX_RETRIES and not success:
        attempts += 1
        # 根据丢包率模拟包丢失
        if random.random() > loss_rate:
            if send_audio_over_main(data_id, audio_path):
                log.append(f"    Attempt {attempts}: packet delivered")
            else:
                log.append(f"    Attempt {attempts}: send failed (channel error)")
        else:
            log.append(f"    Attempt {attempts}: packet lost (simulated)")

        # 等待并轮询控制信道状态
        start_wait = time.time()
        while time.time() - start_wait < TIMEOUT:
            status, _ = get_state(data_id)
            if status == 'received':
                success = True
                log.append(f"    -> Success after {attempts} attempt(s)")
                break
            time.sleep(0.1)

    if not success:
        log.append(f"    -> Failed after {MAX_RETRIES} attempts")

    # 清理数据库记录
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM transmission_states WHERE data_id=?", (data_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return success, log


def run_batch_test(audio_path, loss_rates, num_trials=1000, output_dir="./test_results"):
    """批量测试多个丢包率，统计成功率并输出报告"""
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = os.path.join(output_dir, f"packet_loss_summary_{ts}.txt")
    detail_file = os.path.join(output_dir, f"packet_loss_details_{ts}.txt")

    with open(summary_file, 'w', encoding='utf-8') as f_sum, \
         open(detail_file, 'w', encoding='utf-8') as f_log:

        header = (
            f"Packet Loss Simulation Report\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Audio: {audio_path}\n"
            f"Trials per rate: {num_trials}\n"
            f"Max retries: {MAX_RETRIES}\n"
            f"{'='*60}\n\n"
        )
        f_sum.write(header)
        f_log.write(header)
        print(header)

        table_header = f"{'Loss Rate':>10} | {'Success':>8} | {'Failed':>7} | {'Rate':>8}"
        sep = "-" * len(table_header)
        f_sum.write(table_header + "\n" + sep + "\n")
        print(table_header)
        print(sep)

        results = {}
        for loss_rate in loss_rates:
            print(f"\n[*] Testing loss rate = {loss_rate*100:.0f}% ...")
            f_log.write(f"\n{'='*60}\nLoss Rate: {loss_rate*100:.0f}%\n{'='*60}\n")

            successes = 0
            for trial_id in range(1, num_trials + 1):
                success, log_lines = run_single_trial(loss_rate, audio_path, trial_id)
                if success:
                    successes += 1
                if trial_id % 100 == 0:
                    print(f"    Progress: {trial_id}/{num_trials}")
                # 只记录失败或每50条样本的日志，避免文件过大
                if not success or trial_id % 50 == 0:
                    for line in log_lines:
                        f_log.write(line + "\n")

            rate = successes / num_trials * 100
            summary_line = f"{loss_rate*100:7.0f}%   | {successes:8d} | {num_trials - successes:7d} | {rate:5.1f}%"
            f_sum.write(summary_line + "\n")
            print(f"    Result: {successes}/{num_trials} success ({rate:.1f}%)")
            results[loss_rate] = {'success': successes, 'total': num_trials, 'rate': rate}

        conclusion = "\n" + "="*60 + "\nTest completed.\n"
        f_sum.write(conclusion)
        print(conclusion)

    print(f"\n[+] Summary saved to: {summary_file}")
    print(f"[+] Details saved to: {detail_file}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch packet loss simulation")
    parser.add_argument("audio", help="Path to stego audio WAV file")
    parser.add_argument("--loss", type=float, nargs='+', default=[0.1, 0.2, 0.3],
                        help="Packet loss rates (0-1)")
    parser.add_argument("--trials", type=int, default=1000,
                        help="Number of trials per loss rate")
    parser.add_argument("--output_dir", type=str, default="./test_results",
                        help="Directory for result files")
    args = parser.parse_args()

    print(f"Configuration: audio={args.audio}, loss rates={args.loss}, trials={args.trials}")
    t0 = time.time()
    run_batch_test(args.audio, args.loss, args.trials, args.output_dir)
    print(f"Total time: {time.time() - t0:.1f} sec")