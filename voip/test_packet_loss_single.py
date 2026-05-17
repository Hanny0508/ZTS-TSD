import os
import sys
import time
import random
import threading
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from VoIP.config import DB_PATH
from VoIP.database import init_db, insert_pending, update_to_received, get_state
from VoIP.channel import send_audio_over_main
from VoIP.voip_utils import generate_data_id, current_timestamp, compute_hmac
from VoIP.receiver import Receiver

def simulate_packet_loss(loss_rate, audio_path):
    init_db()
    data_id = generate_data_id()
    timestamp = current_timestamp()
    insert_pending(data_id, timestamp)

    receiver = Receiver(save_dir="./received_audio")
    recv_thread = threading.Thread(target=receiver.start, daemon=True)
    recv_thread.start()
    time.sleep(1)

    attempts = 0
    max_retries = 3
    success = False

    while attempts < max_retries:
        attempts += 1
        if random.random() > loss_rate:
            if send_audio_over_main(data_id, audio_path):
                print(f"Attempt {attempts}: packet delivered")
            else:
                print(f"Attempt {attempts}: send failed")
        else:
            print(f"Attempt {attempts}: packet lost (simulated)")

        time.sleep(2)
        status, _ = get_state(data_id)
        if status == 'received':
            success = True
            break

    if success:
        print(f"Success after {attempts} attempts with loss rate {loss_rate}")
    else:
        print(f"Failed after {attempts} attempts with loss rate {loss_rate}")
    return success

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", help="Path to stego audio file")
    parser.add_argument("--loss", type=float, default=0.2, help="Packet loss rate (0-1)")
    args = parser.parse_args()
    simulate_packet_loss(args.loss, args.audio)