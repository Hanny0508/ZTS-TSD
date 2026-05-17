# dual_channel_covert/channel.py

import socket
import struct
import os
import time
from .config import MAIN_HOST, MAIN_PORT

DATA_ID_LENGTH = 36

def send_audio_over_main(data_id: str, audio_file_path: str, conn: socket.socket = None) -> bool:
    own_conn = False
    if conn is None:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((MAIN_HOST, MAIN_PORT))
        own_conn = True

    try:
        conn.sendall(data_id.encode('utf-8'))
        file_size = os.path.getsize(audio_file_path)
        conn.sendall(struct.pack('>Q', file_size))
        with open(audio_file_path, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                conn.sendall(chunk)
        ack = conn.recv(2)
        return ack == b'OK'
    except Exception as e:
        print(f"[MainChannel] send error: {e}")
        return False
    finally:
        if own_conn:
            conn.close()

def receive_audio_from_main(conn: socket.socket, save_dir: str = "."):
    try:
        data_id_bytes = conn.recv(DATA_ID_LENGTH)
        if len(data_id_bytes) < DATA_ID_LENGTH:
            return None, None
        data_id = data_id_bytes.decode('utf-8')
        size_bytes = conn.recv(8)
        file_size = struct.unpack('>Q', size_bytes)[0]
        save_path = os.path.join(save_dir, f"received_{int(time.time())}.wav")
        received = 0
        with open(save_path, 'wb') as f:
            while received < file_size:
                chunk = conn.recv(min(4096, file_size - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
        if received == file_size:
            conn.sendall(b'OK')
            return data_id, save_path
        else:
            conn.sendall(b'ER')
            return None, None
    except Exception as e:
        print(f"[MainChannel] receive error: {e}")
        return None, None