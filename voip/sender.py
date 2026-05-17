# dual_channel_covert/sender.py

import time
from .config import POLL_INTERVAL, TIMEOUT, MAX_RETRIES
from .database import init_db, insert_pending, get_state
from .channel import send_audio_over_main
from .voip_utils import generate_data_id, current_timestamp, verify_hmac
class Sender:
    def __init__(self, audio_file_path: str):
        self.audio_file = audio_file_path
        init_db()

    def transmit_with_dual_channel(self) -> bool:
        data_id = generate_data_id()
        timestamp = current_timestamp()
        insert_pending(data_id, timestamp)
        print(f"[Sender] transmission initiated, data_id={data_id}")

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"[Sender] attempt {attempt}/{MAX_RETRIES}")
            if not send_audio_over_main(data_id, self.audio_file):
                print("[Sender] main channel send failed")
                continue
            start = time.time()
            while time.time() - start < TIMEOUT:
                status, signature = get_state(data_id)
                if status == 'received':
                    if signature and verify_hmac(data_id, signature):
                        print("[Sender] delivery confirmed")
                        return True
                    else:
                        print("[Sender] invalid signature, retrying")
                        break
                time.sleep(POLL_INTERVAL)
            print("[Sender] timeout or invalid confirmation")
        print("[Sender] max retries reached, transmission failed")
        return False