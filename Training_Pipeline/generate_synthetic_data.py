# generate_synthetic_data.py
#
# Creates synthetic EMG CSV files for training without an Arduino.
# Output format matches collect_gesture_data.py exactly so the training
# pipeline (csv_loader.py -> main.py) works without any changes.
#
# Signal design:
#   rest   - low-amplitude gaussian noise, no oscillation
#   clench - high amplitude, multiple overlapping frequency bands (many motor
#            units firing simultaneously under heavy load)
#   wrist  - moderate amplitude, lower-frequency dominant (lighter load,
#            different muscle group)
#
# After per-window centering in csv_loader.py the three classes differ in:
#   1. Variance (amplitude spread within a 200-sample window)
#   2. Frequency content (which sine bands are present)
#   3. Temporal envelope shape
#
# Usage (run from project root):
#   python Training_Pipeline/generate_synthetic_data.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import csv
import time
from pathlib import Path

SAMPLE_RATE       = 1000   # Hz — matches Arduino sketch
DURATION          = 3.0    # seconds per file — matches collect_gesture_data.py
FILES_PER_GESTURE = 20     # matches SAMPLES_PER_GESTURE in collect_gesture_data.py
BASELINE          = 512    # ADC midpoint (2.5 V on a 5 V rail)


# ---------------------------------------------------------------------------
# Signal generators — return centred signal (ADC units, mean ≈ 0)
# ---------------------------------------------------------------------------

def generate_rest(n, t):
    """Quiet muscle: electrode + amplifier noise only."""
    return np.random.normal(0, 12, n)


def generate_clench(n, t):
    """
    Strong fist: many motor units firing at once.
    High amplitude, broad frequency content (50–260 Hz bands).
    Random phase per file so the model learns the pattern, not a fixed phase.
    """
    noise = np.random.normal(0, 55, n)
    sig  = 72 * np.sin(2 * np.pi *  50 * t + np.random.uniform(0, 2 * np.pi))
    sig += 48 * np.sin(2 * np.pi * 110 * t + np.random.uniform(0, 2 * np.pi))
    sig += 30 * np.sin(2 * np.pi * 180 * t + np.random.uniform(0, 2 * np.pi))
    sig += 18 * np.sin(2 * np.pi * 260 * t + np.random.uniform(0, 2 * np.pi))
    # Slow amplitude modulation — mimics natural tremor / fatigue
    envelope = 1.0 + 0.12 * np.sin(2 * np.pi * 4 * t)
    return sig * envelope + noise


def generate_wrist(n, t):
    """
    Wrist flexion: moderate effort, different muscle group.
    Lower-frequency dominant (20–90 Hz), moderate amplitude.
    Slightly pulsating envelope — wrist holds tend to fluctuate.
    """
    noise = np.random.normal(0, 28, n)
    sig  = 44 * np.sin(2 * np.pi * 22 * t + np.random.uniform(0, 2 * np.pi))
    sig += 30 * np.sin(2 * np.pi * 55 * t + np.random.uniform(0, 2 * np.pi))
    sig += 16 * np.sin(2 * np.pi * 90 * t + np.random.uniform(0, 2 * np.pi))
    envelope = 1.0 + 0.25 * np.sin(2 * np.pi * 2 * t)
    return sig * envelope + noise


GESTURES = {
    'rest':   generate_rest,
    'clench': generate_clench,
    'wrist':  generate_wrist,
}


# ---------------------------------------------------------------------------
# CSV writer — identical format to collect_gesture_data.py
# ---------------------------------------------------------------------------

def write_csv(gesture: str, adc_values: np.ndarray, file_ts: int) -> str:
    Path('data').mkdir(exist_ok=True)
    filename = f'data/data_{gesture}_{file_ts}.csv'
    t_start  = time.time()
    n        = len(adc_values)
    timestamps = [t_start + i / SAMPLE_RATE for i in range(n)]
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'value'])
        writer.writerows(zip(timestamps, adc_values.tolist()))
    return filename


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    n = int(DURATION * SAMPLE_RATE)   # samples per file
    t = np.arange(n) / SAMPLE_RATE    # time axis

    print('=' * 60)
    print('SYNTHETIC EMG DATA GENERATOR')
    print('=' * 60)
    print(f'  {FILES_PER_GESTURE} files x {len(GESTURES)} gestures '
          f'x {DURATION}s @ {SAMPLE_RATE} Hz')
    print(f'  -> {FILES_PER_GESTURE * len(GESTURES)} CSV files in data/\n')

    for gesture, gen_fn in GESTURES.items():
        print(f'  {gesture.upper():<8}', end='', flush=True)
        for i in range(FILES_PER_GESTURE):
            raw = gen_fn(n, t)
            adc = np.clip(BASELINE + raw, 0, 1023).astype(int)
            # Unique timestamp: ms epoch + file index avoids collisions
            file_ts = int(time.time() * 1000) + i
            write_csv(gesture, adc, file_ts)
            print('.', end='', flush=True)
        print(f'  {FILES_PER_GESTURE} files')

    total = FILES_PER_GESTURE * len(GESTURES)
    print(f'\nDone — {total} CSV files written to data/')
    print('\nNext step:')
    print('  python Training_Pipeline/main.py')


if __name__ == '__main__':
    main()
