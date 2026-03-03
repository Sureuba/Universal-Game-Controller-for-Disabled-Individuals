# EMG Gesture Control — User Guide

## What This Does

This system lets you control a computer application using your **muscle signals**.
Three electrodes are placed on your forearm. When you contract your muscles,
the sensor reads the electrical signal, and a neural network figures out which
gesture you are doing — in real time.

You can use it to:
- Play the **Dino Game** (jump, duck, run — controlled by muscle gestures)
- Open the **EMG Canvas** (a visual display that shows your muscle activity as it happens)

---

## What You Need

- A MyoWare 2.0 muscle sensor
- 3 gel electrodes
- An Arduino (connected to your PC via USB)
- Python installed with the required packages

---

## Electrode Placement

1. Clean the skin on your forearm with an alcohol wipe
2. Place the **positive** (+) and **negative** (−) electrodes on the muscle belly,
   about 2 cm apart, along the direction of the muscle fibers
3. Place the **reference** electrode on a bony area (e.g. back of the hand or elbow)
4. Connect the sensor output to Arduino pin A0

---

## First-Time Setup

### Step 1 — Find Your Arduino Port

Open Arduino IDE and check Tools → Port. It will look like:
- Windows: `COM4` (or COM3, COM5, etc.)
- Mac/Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`

Open `Inference/real_time_emg.py` and `Canvas/real_time_emg_canvas.py` and set:
```
ARDUINO_PORT = 'COM4'   # replace with your actual port
```

### Step 2 — Collect Training Data

In the launcher, click **1. Collect Training Data**.

A script will open and guide you through recording each gesture:
- **rest** — arm relaxed, no contraction
- **clench** — make a fist
- **wrist** — flex your wrist upward

For each gesture you will record ~20 samples, each 3 seconds long.
Follow the on-screen countdown. Try to keep the gesture steady while recording.

Tips:
- Sit still and keep your arm resting on a flat surface
- Perform the same gesture the same way each time
- Record in the same position you plan to use during play

### Step 3 — Train the Model

Click **2. Train Model** in the launcher.

This runs in the background and takes about 5–10 minutes.
Watch the console — it will print the accuracy after each epoch.
When it stops, `student_model_best.pth` is ready.

---

## Playing the Dino Game

1. Open the launcher: `python User_interface/simple_launcher.py`
2. Both status indicators should be green
3. Click **▶ DINO GAME**
4. The game window opens. After 2 seconds, EMG control activates.

**Gestures:**
| Gesture | Action |
|---|---|
| clench (fist) | jump |
| wrist flex | duck |
| rest | run (default) |

You can also use keyboard: `SPACE` or `↑` to jump, `↓` to duck.

---

## Using the EMG Canvas

1. Open the launcher: `python User_interface/simple_launcher.py`
2. Click **▶ EMG CANVAS**
3. The canvas window opens. After 2 seconds, EMG control activates.

**What you are seeing:**
- The brush traces a figure-eight path continuously
- **Color** changes based on which gesture the model detects
- **Speed and stroke thickness** change based on how hard you are contracting
  — relaxed muscle barely moves the brush, hard contraction drives it fast
- **Bottom strip** — the raw electrical signal from your muscle in real time
- **Right panel** — confidence percentage and probability bars for each gesture

**Controls:**
- `SPACE` — clear the canvas
- `ESC` — quit

This is the best way to see what the model is actually doing. You can watch the
probability bars shift as you slowly contract and relax your muscle, which shows
the continuous nature of the signal — something the Dino game cannot show.

---

## Troubleshooting

**"Could not open serial port"**
- Check that the Arduino is plugged in
- Check that `ARDUINO_PORT` matches what Arduino IDE shows
- Make sure no other program (Arduino IDE Serial Monitor) has the port open

**Low accuracy / wrong gestures detected**
- Collect more training data (more samples per gesture)
- Make sure electrodes have good contact (re-wet or replace gel pads)
- Re-train after repositioning electrodes if they moved

**Canvas/game opens but nothing happens**
- The EMG runner takes a few seconds to fill the buffer before it starts sending
- Watch the console — it will print "Buffer ready" when it starts

**Model seems to only predict one gesture**
- Your training data may be unbalanced — collect equal samples of each gesture
- Make sure each gesture CSV file is named correctly with the gesture name in it
