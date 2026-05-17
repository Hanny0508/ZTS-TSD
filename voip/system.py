# dual_channel_covert/system.py

import os
import sys
import time
import threading

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'zero-shot-GLS'))
sys.path.insert(0, os.path.join(BASE_DIR, 'TransformerTTS'))
sys.path.insert(0, os.path.join(BASE_DIR, 'naturalspeech3_facodec'))

from .sender import Sender
from .receiver import Receiver

def generate_stego_audio() -> str:
    test_wav = os.path.join(BASE_DIR, "naturalspeech3_facodec", "audio", "1_to_2_vc.wav")
    if not os.path.exists(test_wav):
        raise FileNotFoundError(f"Stego audio not found: {test_wav}")
    print(f"[System] using stego audio: {test_wav}")
    return test_wav

def main():
    print("=" * 50)
    print("Cross-modal Covert Communication System")
    print("=" * 50)

    receiver = Receiver(save_dir=os.path.join(BASE_DIR, "dual_channel_covert", "received_audio"))
    recv_thread = threading.Thread(target=receiver.start, daemon=True)
    recv_thread.start()
    time.sleep(1)

    stego_wav = generate_stego_audio()
    sender = Sender(stego_wav)
    success = sender.transmit_with_dual_channel()

    if success:
        print("[System] secret message transmitted successfully.")
    else:
        print("[System] transmission failed.")

if __name__ == "__main__":
    main()