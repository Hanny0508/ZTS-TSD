# dual_channel_covert/database.py

import sqlite3
import threading
from .config import DB_PATH

_lock = threading.Lock()

def init_db():
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transmission_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                hmac_signature TEXT
            )
        ''')
        conn.commit()
        conn.close()

def insert_pending(data_id: str, timestamp: str):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                "INSERT INTO transmission_states (data_id, timestamp, status) VALUES (?, ?, 'pending')",
                (data_id, timestamp)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

def update_to_received(data_id: str, hmac_signature: str):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE transmission_states SET status='received', hmac_signature=? WHERE data_id=?",
            (hmac_signature, data_id)
        )
        conn.commit()
        conn.close()

def get_state(data_id: str):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT status, hmac_signature FROM transmission_states WHERE data_id=?",
            (data_id,)
        ).fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        return None, None