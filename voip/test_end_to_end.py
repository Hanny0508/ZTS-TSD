import os
import sys
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from VoIP.system import generate_stego_audio
from VoIP.sender import Sender
from VoIP.receiver import Receiver

def end_to_end_test():
    print("Generating stego audio...")
    stego_wav = generate_stego_audio()
    print(f"Stego audio: {stego_wav}")

    receiver = Receiver(save_dir="./received_audio")
    recv_thread = threading.Thread(target=receiver.start, daemon=True)
    recv_thread.start()
    time.sleep(1)

    sender = Sender(stego_wav)
    success = sender.transmit_with_dual_channel()

    if success:
        print("End-to-end test PASSED")
    else:
        print("End-to-end test FAILED")

if __name__ == "__main__":
    end_to_end_test()