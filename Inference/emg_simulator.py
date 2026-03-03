# emg_simulator.py - Test tool for running the canvas or dino game without Arduino
#
# Sends synthetic EMG data through the real model and into the display app via socket,
# exactly as the real EMG runners do. None of the existing code is modified.
#
# What it tests:
#   - EMGBuffer windowing
#   - InterferenceEngine preprocessing + forward pass
#   - Socket connection to canvas or dino game
#   - Canvas rendering and probability bars
#   - Dino game command handling
#
# Usage (start the display app first, then run this):
#   python Inference/emg_simulator.py            -> canvas (port 9998)
#   python Inference/emg_simulator.py dino       -> dino game (port 9999)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
import socket
import json
import math
import numpy as np
import torch

from Inference.emg_buffer import EMGBuffer
from Inference.interference_engine import InterferenceEngine

MODE = 'dino' if (len(sys.argv) > 1 and sys.argv[1] == 'dino') else 'canvas'

CANVAS_PORT = 9998
DINO_PORT   = 9999
SAMPLE_RATE = 200  # simulated samples per second (200 Hz fills buffer fast)

# Cycle of synthetic gestures: (name, duration_seconds, noise_amplitude)
# amplitude = std dev of gaussian noise added to the 512 ADC baseline
#   ~15  = quiet resting muscle
#   ~90  = moderate wrist flex
#   ~180 = strong clench
GESTURE_CYCLE = [
    ('rest',   3.0,  15),
    ('clench', 2.5, 180),
    ('rest',   2.0,  15),
    ('wrist',  2.5,  90),
    ('rest',   2.0,  15),
]


def make_sample(gesture: str, amplitude: float, t: float) -> int:
    """
    One synthetic ADC value (0-1023).
    Active gestures add a 50 Hz sine component to loosely mimic
    motor unit firing frequency seen in real surface EMG.
    """
    noise = np.random.normal(0, amplitude)
    if gesture != 'rest':
        noise += amplitude * 0.3 * math.sin(2 * math.pi * 50 * t)
    return int(np.clip(512 + noise, 0, 1023))


def connect(port: int):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            client.connect(('127.0.0.1', port))
            print(f"[SIM] Connected on port {port}")
            return client
        except ConnectionRefusedError:
            print(f"[SIM] Waiting for app on port {port}...")
            time.sleep(1)


def run():
    port = CANVAS_PORT if MODE == 'canvas' else DINO_PORT
    print(f"[SIM] Simulator starting — target: {MODE.upper()} (port {port})")

    buffer = EMGBuffer(buffer_size=2000, window_size=200)
    engine = InterferenceEngine('student_model_best.pth', device='cpu')
    sock   = connect(port)

    # Pre-fill buffer with resting signal before streaming begins
    print("[SIM] Filling buffer...")
    t = 0.0
    while not buffer.is_ready():
        buffer.add_sample(make_sample('rest', 15, t))
        t += 1 / SAMPLE_RATE

    print("[SIM] Buffer ready — streaming synthetic data\n")
    print("      Gesture cycle: rest → clench → rest → wrist → rest → ...\n")

    idx           = 0
    phase_start   = time.time()
    label, dur, amp = GESTURE_CYCLE[0]
    print(f"[SIM] Phase: REST")

    try:
        while True:
            # Move to next gesture phase when duration expires
            if time.time() - phase_start >= dur:
                idx = (idx + 1) % len(GESTURE_CYCLE)
                label, dur, amp = GESTURE_CYCLE[idx]
                phase_start = time.time()
                print(f"[SIM] Phase: {label.upper()}  (amplitude={amp})")

            buffer.add_sample(make_sample(label, amp, t))
            t += 1 / SAMPLE_RATE
            window = buffer.get_latest_window()

            if MODE == 'canvas':
                window_tensor = engine.preprocess_window(window)
                with torch.no_grad():
                    logits, _ = engine.model(window_tensor, targets=None)
                probs = torch.softmax(logits, dim=-1).squeeze()
                confidence, pred_class = torch.max(probs, dim=-1)
                gesture_pred = engine.gesture_map.get(pred_class.item(), 'unknown')
                prob_dict = {
                    engine.gesture_map.get(i, f'class_{i}'): round(float(p), 3)
                    for i, p in enumerate(probs.tolist())
                }
                packet = {
                    'gesture':       gesture_pred,
                    'confidence':    round(confidence.item(), 3),
                    'probabilities': prob_dict,
                    'raw':           window.tolist(),
                }
                sock.sendall((json.dumps(packet) + '\n').encode())

            else:
                gesture_pred, confidence = engine.predict(window)
                if confidence >= 0.7:
                    command = {'clench': 'jump', 'wrist': 'duck'}.get(gesture_pred, 'run')
                    sock.sendall(command.encode())
                    print(f"[SIM] → {command}  ({gesture_pred} {confidence:.0%})")

            time.sleep(1 / SAMPLE_RATE)

    except (KeyboardInterrupt, BrokenPipeError, OSError):
        print("\n[SIM] Stopped")
    finally:
        sock.close()


if __name__ == '__main__':
    run()
