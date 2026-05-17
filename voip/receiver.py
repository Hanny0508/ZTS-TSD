# dual_channel_covert/receiver.py

import socket
import threading
import os
from .config import MAIN_HOST, MAIN_PORT
from .channel import receive_audio_from_main
from .database import init_db, update_to_received
from .voip_utils import compute_hmac

class Receiver:
    def __init__(self, save_dir: str = "./received_audio"):
        os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir
        init_db()

    def handle_connection(self, conn: socket.socket, addr):
        print(f"[Receiver] connection from {addr}")
        try:
            data_id, audio_path = receive_audio_from_main(conn, self.save_dir)
            if data_id and audio_path:
                print(f"[Receiver] audio saved to {audio_path}, data_id={data_id}")
                signature = compute_hmac(data_id)
                update_to_received(data_id, signature)
                print(f"[Receiver] control channel updated to received, signature={signature[:8]}...")
            else:
                print("[Receiver] audio reception failed")
        except Exception as e:
            print(f"[Receiver] error: {e}")
        finally:
            conn.close()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((MAIN_HOST, MAIN_PORT))
        server.listen(5)
        print(f"[Receiver] main channel listening on {MAIN_HOST}:{MAIN_PORT}")
        try:
            while True:
                conn, addr = server.accept()
                t = threading.Thread(target=self.handle_connection, args=(conn, addr))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("[Receiver] shutting down")
        finally:
            server.close()