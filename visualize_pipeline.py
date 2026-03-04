# visualize_pipeline.py
# Generates emg_pipeline_math.pdf  (2 pages, beginner-friendly)
# Run from project root:  python visualize_pipeline.py

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

OUT = 'emg_pipeline_math.pdf'

BG     = '#0F1117'
W      = '#EEEEEE'
DIM    = '#666666'
BLUE   = '#3A86FF'
GREEN  = '#06D6A0'
ORANGE = '#FF7043'
PURPLE = '#9C6ADE'
RED    = '#EF4444'
YELLOW = '#FFD600'

plt.rcParams.update({
    'figure.facecolor': BG, 'axes.facecolor': BG,
    'text.color': W, 'font.family': 'monospace',
})


def rbox(ax, cx, cy, w, h, title, body='', fc=BLUE, tfs=10, bfs=8):
    """Rounded box with optional subtitle."""
    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle='round,pad=0.03', fc=fc, ec='none', alpha=0.88, zorder=3))
    dy = 0.10 if body else 0
    ax.text(cx, cy + dy, title, ha='center', va='center',
            fontsize=tfs, color=W, fontweight='bold', zorder=4)
    if body:
        ax.text(cx, cy - 0.13, body, ha='center', va='center',
                fontsize=bfs, color='#CCCCCC', zorder=4)


def arrow(ax, x1, y1, x2, y2, label=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=DIM, lw=2.0), zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.08, my, label, fontsize=7.5, color=DIM,
                style='italic', va='center')


def phase_label(ax, x, y, text, col):
    ax.add_patch(FancyBboxPatch(
        (x, y - 0.18), 2.5, 0.36,
        boxstyle='round,pad=0.03', fc=col, ec='none', alpha=0.22, zorder=1))
    ax.text(x + 1.25, y, text, ha='center', va='center',
            fontsize=8.5, color=col, fontweight='bold')


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1  --  File flow: from data to game
# ─────────────────────────────────────────────────────────────────────────────

def page1():
    fig = plt.figure(figsize=(14, 9))
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 9); ax.axis('off')

    fig.text(0.5, 0.965, 'EMG Gesture Classifier  --  How the Files Connect',
             ha='center', va='top', fontsize=15, color=W, fontweight='bold')
    fig.text(0.5, 0.932, 'Follow the arrows from data collection to the live game',
             ha='center', va='top', fontsize=9, color=DIM, style='italic')

    # ── PHASE LABELS ──────────────────────────────────────────────────────
    phase_label(ax, 0.25, 7.95, 'PHASE 1  --  COLLECT', GREEN)
    phase_label(ax, 0.25, 5.85, 'PHASE 2  --  TRAIN',   ORANGE)
    phase_label(ax, 0.25, 3.30, 'PHASE 3  --  RUN LIVE', BLUE)

    # ── PHASE 1: Data collection ──────────────────────────────────────────
    rbox(ax, 5.0, 7.95, 3.8, 0.65,
         'collect_gesture_data.py',
         'Reads Arduino serial, saves one CSV per recording',
         fc=GREEN, tfs=10, bfs=8)

    arrow(ax, 6.9, 7.95, 8.1, 7.95)

    rbox(ax, 9.3, 7.95, 3.0, 0.65,
         'data/  folder',
         'data_rest_123.csv  data_clench_456.csv  ...',
         fc='#1B4332', tfs=10, bfs=7.5)

    # OR path: synthetic data
    ax.text(5.0, 7.28, 'OR  (no Arduino)',
            ha='center', fontsize=8, color=DIM, style='italic')
    rbox(ax, 5.0, 6.88, 3.8, 0.55,
         'generate_synthetic_data.py',
         'Creates fake CSV files that look like EMG signals',
         fc='#1B4332', tfs=9, bfs=7.5)
    arrow(ax, 6.9, 6.88, 8.1, 7.65)

    # ── PHASE 2: Training ─────────────────────────────────────────────────
    arrow(ax, 9.3, 7.62, 9.3, 6.72)
    ax.text(9.55, 7.17, 'feeds into', fontsize=7.5, color=DIM, style='italic')

    rbox(ax, 5.0, 6.35, 3.2, 0.62,
         'csv_loader.py',
         'Reads all CSVs, chops into 200-sample windows',
         fc=PURPLE, tfs=10, bfs=7.5)

    arrow(ax, 5.0, 6.04, 5.0, 5.62, label='windows + labels')

    rbox(ax, 5.0, 5.35, 3.2, 0.55,
         'main.py',
         'Trains the Transformer on those windows',
         fc=ORANGE, tfs=10, bfs=7.5)

    arrow(ax, 6.6, 5.35, 8.0, 5.35, label='saves')

    rbox(ax, 9.5, 5.35, 3.4, 0.62,
         'student_model_best.pth',
         'Saved model weights  (what the model learned)',
         fc='#4A2800', tfs=9.5, bfs=7.5)

    # Architecture support note
    ax.text(2.2, 5.75, 'Architecture/', fontsize=8.5, color=BLUE,
            fontweight='bold', ha='center')
    ax.text(2.2, 5.47, 'defines the shape\nof the model', fontsize=7.5,
            color=DIM, ha='center', linespacing=1.4)
    ax.annotate('', xy=(3.37, 5.35), xytext=(2.75, 5.35),
                arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.3, ls='dashed'))

    # ── PHASE 3 header + model load ──────────────────────────────────────
    arrow(ax, 9.5, 5.04, 9.5, 4.22, label='loaded by')

    rbox(ax, 9.5, 3.95, 3.4, 0.55,
         'interference_engine.py',
         'Loads .pth weights, runs model on each window',
         fc='#2A1A4A', tfs=9, bfs=7.5)

    # emg_buffer
    rbox(ax, 5.0, 3.95, 2.8, 0.55,
         'emg_buffer.py',
         'Collects samples until\n200-sample window is ready',
         fc='#2A1A4A', tfs=9, bfs=7.5)
    arrow(ax, 6.4, 3.95, 8.28, 3.95, label='window [200]')

    # Arduino serial
    rbox(ax, 2.2, 3.95, 2.4, 0.55,
         'Arduino serial',
         '~1000 raw integers\nper second  (0-1023)',
         fc='#1B4332', tfs=9, bfs=7.5)
    arrow(ax, 3.4, 3.95, 4.59, 3.95, label='samples')

    # Two runner scripts
    arrow(ax, 9.5, 3.67, 9.5, 3.1)
    ax.text(9.5, 3.38, 'gesture + confidence', ha='center',
            fontsize=7, color=DIM, style='italic')

    # Dino path
    rbox(ax, 6.8, 2.75, 3.0, 0.58,
         'real_time_emg.py',
         'Dino runner  --  port 9999\nConfidence >= 0.70 to fire',
         fc=BLUE, tfs=9, bfs=7.5)
    ax.plot([9.5, 7.5], [3.1, 3.04], color=DIM, lw=1.5)
    ax.annotate('', xy=(7.5, 3.04), xytext=(7.51, 3.1),
                arrowprops=dict(arrowstyle='->', color=DIM, lw=1.5))

    # Canvas path
    rbox(ax, 12.2, 2.75, 3.0, 0.58,
         'real_time_emg_canvas.py',
         'Canvas runner  --  port 9998\nSends JSON every loop',
         fc=BLUE, tfs=9, bfs=7.5)
    ax.plot([9.5, 11.5], [3.1, 3.04], color=DIM, lw=1.5)
    ax.annotate('', xy=(11.5, 3.04), xytext=(11.49, 3.1),
                arrowprops=dict(arrowstyle='->', color=DIM, lw=1.5))

    # Game boxes
    arrow(ax, 6.8, 2.46, 6.8, 1.88, label='"jump"/"duck"/"run"')
    arrow(ax, 12.2, 2.46, 12.2, 1.88, label='JSON probabilities')

    rbox(ax, 6.8,  1.58, 2.8, 0.58,
         'dino_game.py',
         'Pygame Dino game\nreceives plain string commands',
         fc='#1B4332', tfs=9.5, bfs=7.5)
    rbox(ax, 12.2, 1.58, 2.8, 0.58,
         'canvas_app.py',
         'Pygame visualiser\nshows probabilities + waveform',
         fc='#1B4332', tfs=9.5, bfs=7.5)

    # Launcher note
    ax.add_patch(FancyBboxPatch(
        (0.3, 0.2), 13.4, 0.85,
        boxstyle='round,pad=0.03', fc='#1A1A2E', ec='#333366', lw=1.2))
    ax.text(7.0, 0.62,
            'simple_launcher.py  (User_interface/)  --  GUI that starts any of these scripts for you',
            ha='center', fontsize=9, color=W, fontweight='bold')
    ax.text(7.0, 0.35,
            'You don\'t have to run things manually -- the launcher handles opening the right files in the right order',
            ha='center', fontsize=8, color=DIM)

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2  --  What each group of files does  (plain English)
# ─────────────────────────────────────────────────────────────────────────────

def page2():
    fig = plt.figure(figsize=(14, 9))
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 9); ax.axis('off')

    fig.text(0.5, 0.965, 'What Each Group of Files Does',
             ha='center', va='top', fontsize=15, color=W, fontweight='bold')
    fig.text(0.5, 0.932, 'Plain-English breakdown -- no maths required',
             ha='center', va='top', fontsize=9, color=DIM, style='italic')

    cards = [
        # (col_x, row_y, colour, folder, one-liner, body)
        (0.25, 7.0, GREEN, 'Generated_Files/',
         'Where your recorded training data comes from',
         [
             'collect_gesture_data.py',
             '  Opens the Arduino serial port and listens.',
             '  When you say "go", it records raw numbers',
             '  from your muscle for a few seconds and saves',
             '  them as a CSV file labelled with the gesture.',
             '',
             'You end up with files like:',
             '  data_rest_1234.csv',
             '  data_clench_5678.csv',
             '  data_wrist_9012.csv',
         ]),

        (7.25, 7.0, ORANGE, 'Training_Pipeline/',
         'Turns your CSV files into a trained model',
         [
             'csv_loader.py',
             '  Reads every CSV, chops each recording into',
             '  overlapping 200-sample chunks (windows),',
             '  and attaches the correct gesture label.',
             '',
             'main.py',
             '  Feeds those windows into the model,',
             '  checks how wrong it is (the loss),',
             '  and nudges the model to do better.',
             '  Saves the best result to student_model_best.pth.',
         ]),

        (0.25, 3.5, PURPLE, 'Architecture/',
         'The blueprint that defines the shape of the model',
         [
             'config.py       -- numbers like window size = 200,',
             '                   number of gestures = 3',
             'tokenizer.py    -- splits the 200 samples into',
             '                   10 smaller chunks (patches)',
             'transformer_encoder.py',
             '                -- one attention + MLP layer',
             'student_transformer.py',
             '                -- the full model: tokenizer +',
             '                   4 layers + final classifier',
             '',
             'These files are never run directly.',
             'main.py and inference_engine.py import them.',
         ]),

        (7.25, 3.5, BLUE, 'Inference/  +  Canvas/',
         'Runs the model live using the Arduino',
         [
             'emg_buffer.py',
             '  Acts as a sliding window. Keeps the last',
             '  200 samples ready at all times.',
             '',
             'interference_engine.py',
             '  Loads the saved .pth weights and runs',
             '  the model on each new window.',
             '',
             'real_time_emg.py     -> Dino game (port 9999)',
             'real_time_emg_canvas.py -> Canvas (port 9998)',
             '  Both grab a new window every loop, run the',
             '  model, and send the result to the game.',
         ]),

        (0.25, 0.25, '#1B4332', 'archive/  +  assets/',
         'The game and its graphics',
         [
             'dino_game.py  -- Chrome Dino clone in Pygame.',
             '  Listens on port 9999 for "jump"/"duck"/"run".',
             '',
             'canvas_app.py  -- visualisation window.',
             '  Shows probability bars, waveform, gesture.',
             '',
             'assets/  -- sprites, sounds, fonts used by',
             '  the Dino game.',
         ]),

        (7.25, 0.25, RED, 'student_model_best.pth',
         'The brain  --  what the model actually learned',
         [
             'This file does not exist until you train.',
             '',
             'After training it holds all the numbers',
             '(weights) that make the model able to tell',
             'the difference between rest, clench, and wrist.',
             '',
             'The inference engine loads it at startup.',
             'If this file is missing, live inference crashes.',
             '',
             'student_model_final.pth  -- also saved at the',
             'end of training, but best.pth is the one to use.',
         ]),
    ]

    for (cx, cy, col, folder, oneliner, lines) in cards:
        w, h = 6.5, 3.1
        # background panel
        ax.add_patch(FancyBboxPatch(
            (cx, cy), w, h,
            boxstyle='round,pad=0.04', fc=col, ec='none', alpha=0.18, zorder=1))
        # header bar
        ax.add_patch(FancyBboxPatch(
            (cx, cy + h - 0.60), w, 0.60,
            boxstyle='round,pad=0.03', fc=col, ec='none', alpha=0.55, zorder=2))
        ax.text(cx + 0.18, cy + h - 0.18, folder,
                fontsize=10.5, color=W, fontweight='bold', va='center')
        ax.text(cx + 0.18, cy + h - 0.44, oneliner,
                fontsize=7.5, color='#CCCCCC', va='center')
        # body lines
        ly = cy + h - 0.80
        for line in lines:
            ax.text(cx + 0.22, ly, line,
                    fontsize=7.8, color=W if line and not line.startswith('  ') else '#AAAAAA',
                    va='top')
            ly -= 0.245

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    pages = [
        ('File flow  (data to game)', page1),
        ('What each file group does', page2),
    ]
    print(f'Generating {OUT} ...')
    with PdfPages(OUT) as pdf:
        for name, fn in pages:
            print(f'  page: {name}')
            fig = fn()
            pdf.savefig(fig, bbox_inches='tight', facecolor=BG)
            plt.close(fig)
        pdf.infodict()['Title'] = 'EMG Gesture Classifier -- File Guide'
    print(f'\nDone -- {OUT}')


if __name__ == '__main__':
    main()
