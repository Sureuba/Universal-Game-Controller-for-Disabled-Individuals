# canvas_app.py - EMG Muscle Visualization Canvas
#
# Listens on port 9998 for JSON packets from real_time_emg_canvas.py
#
# What it shows:
#   - Main canvas: Lissajous brush path
#       gesture class  → brush color
#       confidence     → brush speed + stroke width
#       (resting muscle barely moves; hard contraction paints fast and thick)
#   - Bottom strip: scrolling raw EMG waveform
#   - Right sidebar: current gesture, confidence bar, per-class probability bars
#
# Controls: SPACE = clear canvas, ESC = quit

import pygame
import sys
import socket
import threading
import json
import math
from collections import deque

CANVAS_PORT = 9998

# Color palette assigned by gesture index — works for any number of gestures
PALETTE = [
    (255, 100,  80),  # red-orange
    ( 80, 200, 255),  # cyan-blue
    (100, 255, 120),  # lime-green
    (255, 200,  80),  # amber
    (200,  80, 255),  # purple
    (255,  80, 180),  # pink
    ( 80, 255, 220),  # teal
    (255, 140,  40),  # orange
    (140, 255,  80),  # yellow-green
    ( 80, 120, 255),  # indigo
]

# Layout constants
CANVAS_W  = 880
SIDEBAR_X = 880
SIDEBAR_W = 400
WAVE_H    = 130
DRAW_H    = 720 - WAVE_H   # 590 px drawing area


class EMGCanvas:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("EMG Muscle Canvas")
        self.clock = pygame.time.Clock()

        try:
            self.font_lg = pygame.font.Font("assets/PressStart2P-Regular.ttf", 14)
            self.font_sm = pygame.font.Font("assets/PressStart2P-Regular.ttf", 9)
        except FileNotFoundError:
            self.font_lg = pygame.font.Font(None, 28)
            self.font_sm = pygame.font.Font(None, 20)

        # Load gesture names and assign colors by index
        self.gesture_names = ['rest', 'clench', 'wrist']
        try:
            with open('gesture_config.json') as f:
                cfg = json.load(f)
            self.gesture_names = cfg['gestures']
        except Exception:
            pass

        self.gesture_colors = {
            name: PALETTE[i % len(PALETTE)]
            for i, name in enumerate(self.gesture_names)
        }

        # Persistent drawing surface (strokes accumulate here)
        self.canvas_surf = pygame.Surface((CANVAS_W, DRAW_H))
        self.canvas_surf.fill((8, 8, 18))

        # Brush state — parametric Lissajous path
        self.brush_t = 0.0
        self.brush_x = CANVAS_W / 2.0
        self.brush_y = DRAW_H  / 2.0
        self.prev_x  = self.brush_x
        self.prev_y  = self.brush_y

        # EMG state (written by socket thread, read by main thread)
        self._lock         = threading.Lock()
        self._latest       = None
        self.gesture       = self.gesture_names[0]
        self.confidence    = 0.0
        self.probabilities = {n: 0.0 for n in self.gesture_names}
        self.raw_signal    = deque([512] * 200, maxlen=200)

        threading.Thread(target=self._socket_server, daemon=True).start()

    # ── socket ────────────────────────────────────────────────────────────────

    def _socket_server(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('127.0.0.1', CANVAS_PORT))
        srv.listen(1)
        print(f"[CANVAS] Waiting for EMG on port {CANVAS_PORT}...")

        conn, addr = srv.accept()
        print(f"[CANVAS] EMG connected from {addr}")

        buf = ""
        while True:
            try:
                chunk = conn.recv(4096).decode()
                if not chunk:
                    break
                buf += chunk
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    if line.strip():
                        try:
                            with self._lock:
                                self._latest = json.loads(line)
                        except json.JSONDecodeError:
                            pass
            except Exception:
                break

        conn.close()
        print("[CANVAS] EMG disconnected")

    # ── state update ──────────────────────────────────────────────────────────

    def _pull_state(self):
        with self._lock:
            data = self._latest
            self._latest = None
        if data is None:
            return
        self.gesture       = data.get('gesture', self.gesture)
        self.confidence    = data.get('confidence', 0.0)
        self.probabilities = data.get('probabilities', self.probabilities)
        for v in data.get('raw', []):
            self.raw_signal.append(v)

    # ── brush ─────────────────────────────────────────────────────────────────

    def _brush_color(self):
        base  = self.gesture_colors.get(self.gesture, (200, 200, 200))
        alpha = max(0.2, self.confidence)
        return tuple(int(c * alpha) for c in base)

    def _update_brush(self):
        # Key demo point: resting muscle barely moves the brush;
        # hard contraction drives it fast and leaves thick strokes
        speed = 0.0008 + self.confidence * 0.014
        self.brush_t += speed

        cx = CANVAS_W / 2.0
        cy = DRAW_H  / 2.0
        rx = CANVAS_W * 0.42
        ry = DRAW_H  * 0.42

        # Lissajous 3:2 — closed figure that fills the canvas over time
        self.prev_x = self.brush_x
        self.prev_y = self.brush_y
        self.brush_x = cx + rx * math.sin(3 * self.brush_t + math.pi / 4)
        self.brush_y = cy + ry * math.sin(2 * self.brush_t)

    def _draw_stroke(self):
        if self.confidence < 0.12:
            return
        color  = self._brush_color()
        radius = max(2, int(self.confidence * 16))
        pygame.draw.line(
            self.canvas_surf, color,
            (int(self.prev_x), int(self.prev_y)),
            (int(self.brush_x), int(self.brush_y)),
            radius * 2,
        )
        pygame.draw.circle(
            self.canvas_surf, color,
            (int(self.brush_x), int(self.brush_y)),
            radius,
        )

    # ── waveform strip ────────────────────────────────────────────────────────

    def _draw_waveform(self):
        wy = DRAW_H
        pygame.draw.rect(self.screen, (5, 5, 14), (0, wy, CANVAS_W, WAVE_H))

        samples = list(self.raw_signal)
        if len(samples) < 2:
            return

        mid_y  = wy + WAVE_H // 2
        x_step = CANVAS_W / len(samples)
        color  = self.gesture_colors.get(self.gesture, (120, 120, 120))

        pts = [
            (int(i * x_step), int(mid_y - (s / 1023.0 - 0.5) * (WAVE_H * 0.75)))
            for i, s in enumerate(samples)
        ]
        pygame.draw.lines(self.screen, color, False, pts, 1)
        self.screen.blit(self.font_sm.render("RAW EMG", True, (70, 70, 80)), (6, wy + 4))

    # ── sidebar ───────────────────────────────────────────────────────────────

    def _draw_sidebar(self):
        pygame.draw.rect(self.screen, (12, 12, 22), (SIDEBAR_X, 0, SIDEBAR_W, 720))
        PAD   = 18
        x     = SIDEBAR_X + PAD
        bar_w = SIDEBAR_W - PAD * 2
        y     = 20

        # Title
        self.screen.blit(self.font_sm.render("EMG CANVAS", True, (160, 160, 160)), (x, y))
        y += 26
        pygame.draw.line(self.screen, (40, 40, 55), (SIDEBAR_X, y), (1280, y), 1)
        y += 14

        # Current gesture
        color = self.gesture_colors.get(self.gesture, (200, 200, 200))
        self.screen.blit(self.font_lg.render(self.gesture.upper()[:10], True, color), (x, y))
        y += 36

        # Confidence bar
        self.screen.blit(
            self.font_sm.render(f"CONFIDENCE  {self.confidence * 100:.0f}%", True, (140, 140, 140)),
            (x, y),
        )
        y += 18
        pygame.draw.rect(self.screen, (35, 35, 48), (x, y, bar_w, 14))
        pygame.draw.rect(self.screen, color,        (x, y, int(bar_w * self.confidence), 14))
        y += 30
        pygame.draw.line(self.screen, (40, 40, 55), (SIDEBAR_X, y), (1280, y), 1)
        y += 14

        # Per-class probability bars
        self.screen.blit(self.font_sm.render("PROBABILITIES", True, (90, 90, 100)), (x, y))
        y += 20

        for name in self.gesture_names:
            prob = self.probabilities.get(name, 0.0)
            gcol = self.gesture_colors.get(name, (150, 150, 150))

            self.screen.blit(self.font_sm.render(name[:10].upper(), True, gcol), (x, y))
            y += 16
            pygame.draw.rect(self.screen, (35, 35, 48), (x, y, bar_w, 10))
            pygame.draw.rect(self.screen, gcol,         (x, y, int(bar_w * prob), 10))

            pct = self.font_sm.render(f"{prob * 100:.0f}%", True, (90, 90, 100))
            self.screen.blit(pct, (x + bar_w - pct.get_width(), y))
            y += 26

        pygame.draw.line(self.screen, (40, 40, 55), (SIDEBAR_X, y), (1280, y), 1)
        y += 14

        # Color legend
        self.screen.blit(self.font_sm.render("LEGEND", True, (90, 90, 100)), (x, y))
        y += 20

        for name in self.gesture_names:
            gcol = self.gesture_colors.get(name, (150, 150, 150))
            pygame.draw.circle(self.screen, gcol, (x + 6, y + 6), 6)
            self.screen.blit(self.font_sm.render(name[:12].upper(), True, gcol), (x + 18, y))
            y += 22

        # Hint
        self.screen.blit(
            self.font_sm.render("SPACE: clear  ESC: quit", True, (55, 55, 65)),
            (x, 698),
        )

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        print("[CANVAS] EMG canvas started — waiting for signal...")
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_SPACE:
                        self.canvas_surf.fill((8, 8, 18))

            self._pull_state()
            self._update_brush()
            self._draw_stroke()

            self.screen.blit(self.canvas_surf, (0, 0))
            self._draw_waveform()
            self._draw_sidebar()

            self.clock.tick(60)
            pygame.display.update()


if __name__ == '__main__':
    EMGCanvas().run()
