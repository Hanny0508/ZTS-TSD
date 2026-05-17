# dual_channel_covert/utils.py

import uuid
import hmac
import hashlib
import time
import soundfile as sf
import numpy as np
from .config import SHARED_KEY

def generate_data_id() -> str:
    return str(uuid.uuid4())

def current_timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def compute_hmac(data_id: str) -> str:
    return hmac.new(SHARED_KEY, data_id.encode(), hashlib.sha256).hexdigest()

def verify_hmac(data_id: str, signature: str) -> bool:
    expected = compute_hmac(data_id)
    return hmac.compare_digest(expected, signature)

def read_audio(path: str, target_sr: int = 16000) -> np.ndarray:
    data, sr = sf.read(path)
    if sr != target_sr:
        raise ValueError(f"Audio must be {target_sr}Hz, got {sr}Hz")
    if data.ndim > 1:
        data = data[:, 0]
    return data

def write_audio(path: str, audio: np.ndarray, sr: int = 16000):
    sf.write(path, audio, sr)