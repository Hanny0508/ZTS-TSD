# dual_channel_covert/config.py

import os

DB_DIR = os.path.join(os.path.dirname(__file__), "db")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "state.db")

MAIN_HOST = "127.0.0.1"
MAIN_PORT = 50007

POLL_INTERVAL = 1
TIMEOUT = 10
MAX_RETRIES = 3

SHARED_KEY = b"dual_channel_secret_key_2024"