import time
import os
import sys
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from VoIP.sender import Sender
from VoIP.receiver import Receiver
import threading

def measure_latency(audio_path):
    receiver = Receiver(save_dir="./received_audio")
    recv_thread = threading.Thread(target=receiver.start, daemon=True)
    recv_thread.start()
    time.sleep(1)

    sender = Sender(audio_path)

    tracemalloc.start()
    start_time = time.time()
    success = sender.transmit_with_dual_channel()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if success:
        print(f"Transmission successful")
        print(f"Total latency: {end_time - start_time:.3f} seconds")
        print(f"Peak memory usage: {peak / 1024:.2f} KB")
    else:
        print("Transmission failed")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", help="Path to stego audio file")
    args = parser.parse_args()
    measure_latency(args.audio)