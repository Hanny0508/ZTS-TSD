你可以直接复制下面的内容，粘贴到 `VoIP/README.md` 里。这是完整的、格式正确的 README。

```markdown
# Dual-Channel Covert Communication System

Implementation of the dual-channel architecture described in the paper "Cross-modal Covert Communication Based on Autoregressive Models".

## Architecture

```
Sender                                        Receiver
  │                                              │
  │  Main Channel (VoIP stream)                  │
  │  ──────────── audio + data_id ────────────►  │
  │                                              │
  │  Control Channel (shared database)           │
  │  ◄──────── state synchronization ────────►   │
  │                                              │
```

- **Main Channel**: TCP-based simulated VoIP transmission carrying stego audio and a unique `data_id`.
- **Control Channel**: A shared SQLite database maintaining transmission state (`pending` / `received`) protected by HMAC signatures. The sender polls this channel for delivery confirmation and triggers retransmission on timeout or signature mismatch.

## Dependencies

- Python 3.8+
- `soundfile`
- `numpy`

Install requirements:

```bash
pip install -r requirements.txt
```

## Project Structure

```
VoIP/
├── config.py              Parameters and shared key
├── database.py            Database operations for the control channel
├── channel.py             Main channel send/receive logic
├── sender.py              Sender module with retransmission
├── receiver.py            Receiver module (multi-threaded)
├── voip_utils.py          UUID, HMAC, audio I/O utilities
├── system.py              Full pipeline integration entry point
├── test_latency.py        Measure latency and memory overhead
├── test_packet_loss.py    Simulate packet loss and test robustness
├── test_end_to_end.py     End-to-end integration test
├── __init__.py            Package marker
├── requirements.txt       Python dependencies
└── README.md
```

## Usage

Ensure the parent modules (`zero-shot-GLS`, `TransformerTTS`, `naturalspeech3_facodec`) are in place and functional.  
Place the stego audio file (e.g., `1_to_2_vc.wav`) in `naturalspeech3_facodec/audio/`.

### Run the complete system

From the project root directory (`zsctsd/master/`):

```bash
python -m VoIP.system
```

This starts the receiver in a background thread, loads/generates the stego audio, and transmits it via the dual-channel scheme.

### Run receiver and sender separately

**Terminal 1 (receiver):**
```bash
python -c "from VoIP.receiver import Receiver; Receiver().start()"
```

**Terminal 2 (sender):**
```bash
python -c "from VoIP.sender import Sender; Sender('naturalspeech3_facodec/audio/1_to_2_vc.wav').transmit_with_dual_channel()"
```

You can replace the audio path with your own file.

### Run tests

**Latency and memory overhead measurement:**
```bash
python -m VoIP.test_latency path/to/stego.wav
```

**Packet loss simulation (e.g., 30% loss rate):**
```bash
python -m VoIP.test_packet_loss path/to/stego.wav --loss 0.3
```

**End-to-end system test:**
```bash
python -m VoIP.test_end_to_end
```

## Key Mechanisms

- **Redundant synchronization**: The control channel maintains a state table with unique `data_id`, timestamp, status, and HMAC signature.
- **Integrity verification**: HMAC-SHA256 computed over `data_id` using a pre-shared key prevents state tampering.
- **Reliable delivery**: The sender polls the control channel for `received` status; if the valid signature is missing within `TIMEOUT`, the audio is retransmitted up to `MAX_RETRIES` times.

## Configuration

Modify `VoIP/config.py` to change network settings, polling interval, timeouts, or the shared secret.

## Database Inspection

Use the SQLite command line to view transmission states:

```bash
sqlite3 VoIP/db/state.db "SELECT * FROM transmission_states;"
```

batch test use
```
python test_packet_loss.py "master\naturalspeech3_facodec\audio\1_to_2_vc.wav" --loss 0.1 0.2 0.3 --trials 1000
```