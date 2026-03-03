# real_time_emg_canvas.py - EMG runner for the canvas visualizer
#
# Same pipeline as Inference/real_time_emg.py but sends rich JSON packets
# instead of simple command strings, because the canvas needs:
#   - full softmax probability distribution (not just the winning class)
#   - continuous confidence score (no threshold gate)
#   - raw ADC signal (for the waveform strip)
#
# Flow: Arduino -> EMGBuffer -> one forward pass -> JSON -> canvas_app.py (port 9998)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import serial
import time
import socket
import json
import torch
from Inference.emg_buffer import EMGBuffer
from Inference.interference_engine import InterferenceEngine


ARDUINO_PORT = ''   # fill in your COM port e.g. 'COM4'
BAUD_RATE    = 9600

CANVAS_HOST  = '127.0.0.1'
CANVAS_PORT  = 9998


def connect_to_canvas():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            client.connect((CANVAS_HOST, CANVAS_PORT))
            print(f"[EMG] Connected to canvas at {CANVAS_HOST}:{CANVAS_PORT}")
            return client
        except ConnectionRefusedError:
            print("[EMG] Canvas not ready, retrying...")
            time.sleep(1)


def run():
    print("[EMG] Starting canvas EMG control")

    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE)
    ser.reset_input_buffer()
    time.sleep(2)
    print(f"[EMG] Arduino connected on {ARDUINO_PORT}")

    buffer = EMGBuffer(buffer_size=2000, window_size=200)
    engine = InterferenceEngine('student_model_best.pth', device='cpu')

    canvas_socket = connect_to_canvas()

    # Fill buffer before streaming
    print("[EMG] Filling buffer...")
    while not buffer.is_ready():
        line = ser.readline().decode('latin-1').strip()
        try:
            buffer.add_sample(int(line))
        except ValueError:
            continue

    print("[EMG] Buffer ready - streaming to canvas")
    print("[EMG] Format:  GESTURE  confidence  |  rest:%  clench:%  wrist:%\n")

    last_print = 0.0

    try:
        while True:
            line = ser.readline().decode('latin-1').strip()
            try:
                value = int(line)
            except ValueError:
                continue

            buffer.add_sample(value)
            window = buffer.get_latest_window()

            # Single forward pass - extract full softmax distribution
            window_tensor = engine.preprocess_window(window)
            with torch.no_grad():
                logits, _ = engine.model(window_tensor, targets=None)

            probs = torch.softmax(logits, dim=-1).squeeze()
            confidence, pred_class = torch.max(probs, dim=-1)

            gesture_id = pred_class.item()
            gesture    = engine.gesture_map.get(gesture_id, f'class_{gesture_id}')

            prob_dict = {
                engine.gesture_map.get(i, f'class_{i}'): round(float(p), 3)
                for i, p in enumerate(probs.tolist())
            }

            # Print status once per second
            now = time.time()
            if now - last_print >= 1.0:
                bars = '  '.join(f"{k}:{v:.0%}" for k, v in prob_dict.items())
                print(f"[EMG] {gesture.upper():<8} {confidence.item():.0%}  |  {bars}")
                last_print = now

            packet = {
                'gesture':       gesture,
                'confidence':    round(confidence.item(), 3),
                'probabilities': prob_dict,
                'raw':           window.tolist(),  # all 200 ADC samples for waveform
            }

            try:
                canvas_socket.sendall((json.dumps(packet) + '\n').encode())
            except (BrokenPipeError, OSError):
                print("[EMG] Canvas disconnected")
                break

    except KeyboardInterrupt:
        print("\n[EMG] Stopping")
    finally:
        ser.close()
        canvas_socket.close()
        print("[EMG] Closed")


if __name__ == '__main__':
    run()
