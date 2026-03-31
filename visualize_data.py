import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / 'data'

GESTURES = ['rest', 'clench', 'wrist']
COLORS   = ['steelblue', 'crimson', 'seagreen']

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)
fig.suptitle('EMG Signal by Gesture — all files overlaid', fontsize=14, fontweight='bold')

for ax, gesture, color in zip(axes, GESTURES, COLORS):
    files = sorted(DATA_DIR.glob(f'data_{gesture}_*.csv'))
    if not files:
        ax.set_title(f'{gesture.upper()} — no files found', color='red')
        continue

    all_values = []
    for f in files:
        df = pd.read_csv(f)
        values = df['value'].values
        # normalize same way as training
        v = (values / 4095.0) * 3.3
        v = (v - np.mean(v)) * 1000  # center + mV
        all_values.append(v)
        ax.plot(v, alpha=0.15, color=color, linewidth=0.8)

    # mean across files (truncate to shortest)
    min_len = min(len(v) for v in all_values)
    mean_signal = np.mean([v[:min_len] for v in all_values], axis=0)
    ax.plot(mean_signal, color='black', linewidth=1.5, label='mean')

    ax.set_title(f'{gesture.upper()}  ({len(files)} files)', fontweight='bold')
    ax.set_ylabel('mV (centered)')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel('Sample index')
plt.tight_layout()
plt.show()
