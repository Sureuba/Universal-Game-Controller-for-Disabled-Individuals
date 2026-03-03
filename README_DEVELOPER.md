# EMG Gesture Classifier — Developer Guide

## What This Is

A real-time EMG (electromyography) gesture recognition system. A MyoWare muscle sensor
connected to an Arduino reads raw analog voltage from muscle contractions. A lightweight
Transformer neural network classifies the signal into gestures live, and sends those
predictions to a display application (a Dino game or a visualization canvas).

---

## Hardware

- Arduino (any model with analog input)
- MyoWare 2.0 muscle sensor
- 3 electrodes: positive, negative, reference (single-channel)
- USB connection to PC (Bluetooth planned)

The Arduino sketch just does `Serial.println(analogRead(A0))` at ~1000 Hz.
Each line is one integer 0–1023 (10-bit ADC).

---

## Project Structure

```
research/
│
├── Architecture/               # Model definition (no data, no weights)
│   ├── config.py               # All hyperparameters with paper citations
│   ├── tokenizer.py            # Conv1d patch tokenizer + positional embedding
│   ├── transformer_encoder.py  # Single transformer Block (attention + feedforward)
│   └── student_transformer.py  # Full model: tokenizer → 4 blocks → classifier head
│
├── Training_Pipeline/          # Offline training
│   ├── csv_loader.py           # Loads CSVs, windows them, returns tensors
│   └── main.py                 # Training loop with early stopping
│
├── Inference/                  # Live inference with Arduino
│   ├── emg_buffer.py           # Circular deque, collects samples until window is ready
│   ├── interference_engine.py  # Loads weights, preprocesses window, runs forward pass
│   └── real_time_emg.py        # Glue: serial → buffer → engine → socket (port 9999)
│
├── Canvas/                     # EMG visualization app
│   ├── canvas_app.py           # Pygame canvas, listens on port 9998
│   └── real_time_emg_canvas.py # serial → buffer → engine → JSON socket (port 9998)
│
├── Setup/
│   └── gesture_setup_gui.py    # tkinter GUI to configure gestures (optional/dino only)
│
├── User_interface/
│   └── simple_launcher.py      # Main launcher GUI
│
├── Generated_Files/
│   ├── gesture_mapping.py      # Auto-generated: gesture index → name → command
│   └── collect_gesture_data.py # Auto-generated: data collection script
│
├── archive/
│   └── dino_game.py            # Pygame Dino game, listens on port 9999
│
├── data/                       # Recorded CSV files (one per gesture recording)
├── assets/                     # Fonts, sprites, sounds for the Dino game
├── gesture_config.json         # Active gesture configuration
├── student_model_best.pth      # Best saved weights (by val loss)
└── student_model_final.pth     # Final epoch weights
```

---

## Signal Pipeline (step by step)

### 1. Tokenization — `Architecture/tokenizer.py`

The raw window is shape `[1, 1, 200]` (batch=1, channels=1, samples=200).

A `Conv1d` with `kernel_size=20, stride=20` slices it into **10 non-overlapping patches**
of 20 samples each, and projects each patch into a 128-dimensional embedding.
Positional embeddings are added so the model knows patch order.

Output: `[1, 10, 128]` — 10 tokens, each with 128 features.

### 2. Transformer Blocks — `Architecture/transformer_encoder.py`

4 stacked `Block` objects, each containing:
- Multi-head self-attention (4 heads, 32 dims each)
- Layer norm
- Feedforward MLP (128 → 512 → 128)
- Residual connections

The blocks let the model learn which time patches matter for each gesture
(e.g., the rising edge of a clench vs. a sustained wrist flex).

### 3. Classification — `Architecture/student_transformer.py`

After the blocks, all 10 tokens are mean-pooled into one 128-dim summary vector.
A linear layer maps it to `num_gestures` logit scores.
During inference, softmax turns these into probabilities.

### 4. Preprocessing — `Inference/interference_engine.py`

Before the window enters the model:
```
raw ADC (0–1023) → voltage (0–5V) → center at zero → millivolts → reshape to [1,1,200]
```
Centering removes each person's unique baseline offset, which helps cross-user generalization.

### 5. Buffering — `Inference/emg_buffer.py`

The Arduino produces one sample per ~1ms. The model needs 200 samples at once.
`EMGBuffer` is a `deque(maxlen=2000)`. Every new sample is appended; the oldest drops off.
`get_latest_window()` returns the last 200 samples as a numpy array.

### 6. Real-time loop — `Inference/real_time_emg.py` or `Canvas/real_time_emg_canvas.py`

```
while True:
    read one line from Arduino serial
    add to buffer
    get latest 200-sample window
    run forward pass
    send result to display app via TCP socket
```

The **dino runner** applies a 0.7 confidence threshold and sends plain strings
(`"jump"`, `"duck"`, `"run"`) to port 9999.

The **canvas runner** has no threshold — it sends a JSON packet every loop iteration:
```json
{
  "gesture": "clench",
  "confidence": 0.87,
  "probabilities": {"rest": 0.05, "clench": 0.87, "wrist": 0.08},
  "raw": [512, 518, ...]
}
```

---

## Socket Protocol

Both display apps act as TCP servers. The EMG runner connects as a client.

| App | Port | Format |
|---|---|---|
| `archive/dino_game.py` | 9999 | plain string (`"jump"\n`) |
| `Canvas/canvas_app.py` | 9998 | JSON + newline |

The display app starts first and waits. The launcher opens the app, waits 2 seconds,
then starts the EMG runner which connects to it.

---

## Training

Data lives in `data/` as CSV files named `data_<gesture>_<timestamp>.csv`.
Each file has columns `[timestamp, value]`.

`csv_loader.py` loads all CSVs, infers the gesture label from the filename,
then windows each file with 75% overlap (stride = 50 samples, window = 200).
It returns an 80/20 train/val split by file (not by window, to avoid data leakage).

`main.py` runs the training loop with AdamW, cross-entropy loss, and early stopping
(patience=10 epochs). Best weights are saved to `student_model_best.pth`.

---

## Key Config Values (`Architecture/config.py`)

| Parameter | Value | Why |
|---|---|---|
| `window_size` | 200 | 200ms at 1kHz — captures full gesture dynamics |
| `patch_size` | 20 | 10 tokens per window — reduces attention cost |
| `n_embed` | 128 | Target ~300K parameters for edge deployment |
| `n_head` | 4 | Must divide evenly into n_embed |
| `n_layer` | 4 | Enough depth without overfitting small datasets |
| `overlap` | 0.75 | 75% overlap during training windowing |
| `num_gestures` | 3 | rest, clench, wrist |

---

## How to Run Without the Launcher

```bash
# Terminal 1 — start the display app first
python Canvas/canvas_app.py
# or
python archive/dino_game.py

# Terminal 2 — start the EMG runner (set ARDUINO_PORT first)
python Canvas/real_time_emg_canvas.py
# or
python Inference/real_time_emg.py
```

Set `ARDUINO_PORT` at the top of the runner script (e.g. `'COM4'` on Windows,
`'/dev/ttyUSB0'` on Linux).

---

## Planned / Not Yet Implemented

- **Signal preprocessing**: bandpass filter 20–450 Hz, notch at 60 Hz (powerline noise)
- **Multi-channel**: current architecture supports it (`num_channels` in config), just needs wiring
- **Knowledge distillation**: train a 15M-param teacher, distill to this 300K student
- **Bio-Vault**: cosine-similarity cache for zero-shot new-user adaptation
- **Bluetooth**: replace `serial` with a BLE library

---

## Developer FAQ

**Q: I changed a hyperparameter in `config.py`. Do I need to retrain?**

Yes, always. The `.pth` weights file is tied to the exact architecture it was trained with.
If you change `n_embed`, `n_head`, `n_layer`, `num_gestures`, `patch_size`, or `window_size`,
the saved weights will no longer match the model shape and PyTorch will throw an error on load.
Delete `student_model_best.pth` and retrain from scratch.

---

**Q: Training finishes but val accuracy is stuck around 33%. What's wrong?**

33% for 3 classes means the model is guessing randomly — it learned nothing.
Common causes:
- Gesture names in `collect_gesture_data.py` don't match what `csv_loader.py` looks for
  (`rest`/`clench`/`wrist`). Check the filenames in `data/`.
- Not enough data — aim for at least 10 CSV files per gesture, 20+ is better.
- All recordings look the same (e.g. you tensed during "rest" takes). Re-record with clean,
  distinct gestures.
- Class imbalance — `csv_loader.py` prints counts per class. If one class has far fewer
  windows, re-record that gesture.

---

**Q: The model trains well but performs badly live. What's the mismatch?**

The most common causes:
- Electrode placement shifted between recording and live use. The model learns your specific
  placement. Reposition exactly as during recording, or re-record.
- Preprocessing mismatch — training and inference both now center per-window (fixed), but
  if you have old `.pth` weights trained before that fix, retrain.
- Confidence threshold too high — lower `CONFIDENCE_THRESHOLD` in `real_time_emg.py`
  from 0.7 to 0.5 to see if predictions start coming through.

---

**Q: `csv_loader.py` finds 0 files and training crashes. Why?**

The loader globs for exactly `data_rest_*.csv`, `data_clench_*.csv`, `data_wrist_*.csv`.
Check that:
1. Files are inside the `data/` folder at the project root.
2. Filenames contain the gesture name in that exact position: `data_<gesture>_<timestamp>.csv`.
3. `GESTURES` in `collect_gesture_data.py` is `['rest', 'clench', 'wrist']` — not the old
   `['jump', 'duck', 'run']` from before the fix.

---

**Q: The canvas or dino game opens but nothing happens from EMG.**

The display app starts first and listens on a socket. The EMG runner connects to it.
Check that:
1. The EMG runner started (check console — it prints "Buffer ready").
2. Ports are not already in use. If you crashed a previous session, the OS may hold the port
   for ~30 seconds. Just wait or restart.
3. `ARDUINO_PORT` is set correctly in the runner script. The runner will silently hang
   waiting for serial data if the port is wrong.

---

**Q: I get `ModuleNotFoundError` when running any script.**

All scripts are designed to be run from the **project root** (`research/`), not from inside
their own subdirectory. Always run as:
```bash
# correct
python Training_Pipeline/main.py

# wrong — will break imports
cd Training_Pipeline
python main.py
```
The imports like `from Architecture.student_transformer import ...` rely on the root being
on the Python path, which only works when you run from the root.

---

**Q: What does the attention scaling fix change practically?**

Before the fix, attention scores were divided by `sqrt(128)` ≈ 11.3.
After the fix, they are divided by `sqrt(32)` ≈ 5.66 (the actual key/query dimension).
The smaller divisor means attention logits are less aggressively flattened before softmax,
so the model can form sharper attention patterns — certain time patches get higher weight.
With only 10 tokens this is a subtle effect, but it is the mathematically correct formulation
from the original "Attention Is All You Need" paper. Retrain after this change.

---

**Q: Can I add a 4th gesture without breaking everything?**

Yes, but several places need updating in sync:
1. `Architecture/config.py` — `num_gestures = 4`
2. `Generated_Files/collect_gesture_data.py` — add the new gesture name to `GESTURES`
3. `Training_Pipeline/csv_loader.py` — add the new gesture to `gesture_map` and the
   `files_by_gesture` dict
4. `Inference/interference_engine.py` — update the fallback `GESTURE_MAP`
5. Re-collect data for all gestures and retrain from scratch

---

**Q: Why is there both `student_model_best.pth` and `student_model_final.pth`?**

`best` is saved whenever validation loss improves during training — it is the checkpoint
with the lowest overfitting. `final` is saved at the very end of training regardless.
The inference engine loads `best` by default. `final` is useful if you want to inspect
where training ended up, but `best` is almost always the one to deploy.

---

**Q: The dino game runner has a 0.7 confidence threshold. The canvas runner has none. Why?**

The dino game needs discrete events — a jump either happens or it doesn't. A 70% threshold
prevents noisy low-confidence predictions from triggering unwanted actions and adds a 0.5s
cooldown so one contraction doesn't fire multiple jumps.

The canvas is a continuous visualizer. The whole point is to show the signal at all
confidence levels — including the transition while you're ramping up a contraction.
Gating it would defeat the purpose.

---

**Q: How do I run this on a machine without a GPU?**

It already defaults to CPU (`device='cpu'` in `interference_engine.py`). The model is
~300K parameters and inference on a 200-sample window takes well under 10ms on any modern
CPU, so GPU is not needed for real-time use. GPU only meaningfully helps during training
if you have a very large dataset.
