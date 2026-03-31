# dino_game.py - Full game with EMG socket control
import pygame
import sys
import random
import socket
import threading
import json
import os
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

W, H        = 1280, 720
GROUND_Y    = 360
DINO_GROUND = 360
FPS         = 120

# ── Colours ──────────────────────────────────────────────────────────────────
SKY_TOP    = (108, 189, 237)
SKY_BOT    = (215, 238, 252)
EARTH_COL  = (160, 120,  68)
EARTH_DARK = (115,  82,  38)
SCORE_COL  = ( 55,  55,  55)
HI_COL     = (145, 145, 145)
EMG_COL    = ( 50, 120, 220)   # blue badge
KB_COL     = ( 50, 175,  70)   # green badge

SCORES_FILE = 'dino_scores.json'


# ── Score persistence ─────────────────────────────────────────────────────────
def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_score(score, mode):
    if int(score) <= 0:
        return
    scores = load_scores()
    scores.append({
        'score': int(score),
        'mode':  mode,
        'date':  datetime.now().strftime('%Y-%m-%d'),
    })
    scores.sort(key=lambda x: x['score'], reverse=True)
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores[:25], f, indent=2)


# ── Sky gradient ──────────────────────────────────────────────────────────────
def _make_sky(w, h):
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
    return surf


# ── App ───────────────────────────────────────────────────────────────────────
class App:
    """Top-level coordinator: manages all screens and shared state."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("EMG Dino — Universal Game Controller")
        self.clock  = pygame.time.Clock()

        try:
            self.font_lg = pygame.font.Font("assets/PressStart2P-Regular.ttf", 22)
            self.font    = pygame.font.Font("assets/PressStart2P-Regular.ttf", 16)
            self.font_sm = pygame.font.Font("assets/PressStart2P-Regular.ttf", 11)
        except Exception:
            self.font_lg = pygame.font.Font(None, 34)
            self.font    = pygame.font.Font(None, 26)
            self.font_sm = pygame.font.Font(None, 20)

        self.sky_surf  = _make_sky(W, GROUND_Y + 24)
        self.ground_img = pygame.transform.scale(
            pygame.image.load("assets/ground.png"), (W, 20))
        self.cloud_img  = pygame.transform.scale(
            pygame.image.load("assets/cloud.png"), (200, 80))

        try:
            self.death_sfx  = pygame.mixer.Sound("assets/sfx/lose.mp3")
            self.points_sfx = pygame.mixer.Sound("assets/sfx/100points.mp3")
            self.jump_sfx   = pygame.mixer.Sound("assets/sfx/jump.mp3")
        except Exception:
            print("[WARNING] Could not load sound files")
            self.death_sfx = self.points_sfx = self.jump_sfx = None

        self.CLOUD_EVENT = pygame.USEREVENT
        pygame.time.set_timer(self.CLOUD_EVENT, 3000)

        # EMG socket state
        self.emg_connected   = False
        self._socket_started = False

        # Calibration state
        self._glow   = {'rest': 0, 'clench': 0, 'wrist': 0}   # frames remaining
        self._tested = {'rest': False, 'clench': False, 'wrist': False}
        self._sigbar = 0.0   # 0-1, decays each frame

        # Shared decorative background elements
        self._menu_clouds = pygame.sprite.Group()
        self._menu_dino   = Dino(160, DINO_GROUND)
        self._menu_gx     = 0   # ground scroll x for menu screens

    # ── Socket server ─────────────────────────────────────────────────────────
    def _socket_server(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind(('127.0.0.1', 9999))
            srv.listen(1)
            print("[SOCKET] Waiting for EMG on port 9999...")
            conn, addr = srv.accept()
            self.emg_connected = True
            print(f"[SOCKET] EMG connected from {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                cmd = data.decode().strip()
                print(f"[EMG] {cmd}")
                if   cmd == "jump": pygame.event.post(pygame.event.Event(pygame.USEREVENT + 1))
                elif cmd == "duck": pygame.event.post(pygame.event.Event(pygame.USEREVENT + 2))
                elif cmd == "run":  pygame.event.post(pygame.event.Event(pygame.USEREVENT + 3))
            conn.close()
            self.emg_connected = False
        except Exception as e:
            print(f"[SOCKET] {e}")
        finally:
            srv.close()

    def start_emg(self):
        if not self._socket_started:
            threading.Thread(target=self._socket_server, daemon=True).start()
            self._socket_started = True

    # ── Shared drawing helpers ────────────────────────────────────────────────
    def _draw_bg(self):
        self.screen.blit(self.sky_surf, (0, 0))
        pygame.draw.rect(self.screen, EARTH_COL,  (0, GROUND_Y + 18, W, H - GROUND_Y - 18))
        pygame.draw.rect(self.screen, EARTH_DARK, (0, GROUND_Y + 13, W, 6))

    def _draw_ground(self, gx):
        self.screen.blit(self.ground_img, (gx,     GROUND_Y))
        self.screen.blit(self.ground_img, (gx + W, GROUND_Y))

    def _draw_menu_scene(self):
        """Animated background shared by menu / calibration / scoreboard."""
        self._menu_gx -= 1
        if self._menu_gx <= -W:
            self._menu_gx = 0
        self._draw_bg()
        self._menu_clouds.update(0.5)
        self._menu_clouds.draw(self.screen)
        self._menu_dino.update()
        self.screen.blit(self._menu_dino.image, self._menu_dino.rect)
        self._draw_ground(self._menu_gx)

    def _btn(self, rect, label, col, hover_col, font=None):
        """Draw a button. Returns True if hovered."""
        font  = font or self.font_sm
        mouse = pygame.mouse.get_pos()
        hov   = rect.collidepoint(mouse)
        pygame.draw.rect(self.screen, hover_col if hov else col, rect, border_radius=8)
        border = tuple(min(255, c + 55) for c in (hover_col if hov else col))
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)
        lbl = font.render(label, True, (240, 240, 240))
        self.screen.blit(lbl, lbl.get_rect(center=rect.center))
        return hov

    def _clicked(self, rect, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and rect.collidepoint(event.pos))

    # ── Main menu ─────────────────────────────────────────────────────────────
    def show_main_menu(self):
        """Returns 'emg', 'keyboard', or 'scoreboard'."""
        emg_btn = pygame.Rect(W // 2 - 230, 290, 460, 66)
        kb_btn  = pygame.Rect(W // 2 - 230, 380, 460, 66)
        sc_btn  = pygame.Rect(W // 2 - 160, 475, 320, 46)

        scores   = load_scores()
        best_all = scores[0]['score'] if scores else 0

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == self.CLOUD_EVENT:
                    self._menu_clouds.add(
                        Cloud(self.cloud_img, W + 100, random.randint(50, 280)))
                if self._clicked(emg_btn, event) or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_1):
                    return 'emg'
                if self._clicked(kb_btn, event) or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_2):
                    return 'keyboard'
                if self._clicked(sc_btn, event):
                    return 'scoreboard'

            self._draw_menu_scene()

            # Title
            title = self.font_lg.render("EMG  DINO", True, (35, 35, 48))
            self.screen.blit(title, title.get_rect(center=(W // 2, 175)))

            sub = self.font_sm.render(
                "Universal Game Controller for Disabled Individuals",
                True, (75, 100, 145))
            self.screen.blit(sub, sub.get_rect(center=(W // 2, 228)))

            # Best score
            if best_all:
                best_surf = self.font_sm.render(
                    f"ALL-TIME BEST: {best_all:,}", True, (200, 170, 50))
                self.screen.blit(best_surf, best_surf.get_rect(center=(W // 2, 258)))

            # Mode buttons
            self._btn(emg_btn, "1   EMG MUSCLE CONTROL",
                      (38, 95, 185), (62, 128, 228), self.font_sm)
            self._btn(kb_btn,  "2   KEYBOARD  /  MOUSE",
                      (38, 150, 62), (55, 190, 80), self.font_sm)

            # Sub-labels under buttons
            emg_desc = self.font_sm.render(
                "CLENCH = jump     WRIST = duck", True, (80, 110, 170))
            kb_desc  = self.font_sm.render(
                "SPACE / UP = jump     DOWN = duck", True, (60, 140, 75))
            self.screen.blit(emg_desc, emg_desc.get_rect(
                center=(W // 2, emg_btn.bottom + 12)))
            self.screen.blit(kb_desc,  kb_desc.get_rect(
                center=(W // 2, kb_btn.bottom + 12)))

            self._btn(sc_btn, "SCOREBOARD", (75, 55, 110), (105, 78, 148), self.font_sm)

            hint = self.font_sm.render("Press 1 or 2 to select", True, (100, 100, 120))
            self.screen.blit(hint, hint.get_rect(center=(W // 2, sc_btn.bottom + 22)))

            self.clock.tick(FPS)
            pygame.display.update()

    # ── EMG Calibration ───────────────────────────────────────────────────────
    def show_calibration(self):
        """Show EMG signal calibration. Returns 'start' or 'back'."""
        self._glow   = {'rest': 0, 'clench': 0, 'wrist': 0}
        self._tested = {'rest': False, 'clench': False, 'wrist': False}
        self._sigbar = 0.0

        start_btn = pygame.Rect(W // 2 - 145, H - 105, 290, 54)
        back_btn  = pygame.Rect(30, H - 72, 180, 42)
        dot_tick  = 0   # for the animated waiting dots

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == self.CLOUD_EVENT:
                    self._menu_clouds.add(
                        Cloud(self.cloud_img, W + 100, random.randint(50, 280)))
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'back'
                    if event.key == pygame.K_RETURN:
                        return 'start'
                if self._clicked(back_btn, event):
                    return 'back'
                if self._clicked(start_btn, event):
                    return 'start'

                # EMG gesture events
                if event.type == pygame.USEREVENT + 1:   # clench → jump
                    self._tested['clench'] = True
                    self._glow['clench']   = 48
                    self._sigbar           = 1.0
                if event.type == pygame.USEREVENT + 2:   # wrist → duck
                    self._tested['wrist'] = True
                    self._glow['wrist']   = 48
                    self._sigbar          = 1.0
                if event.type == pygame.USEREVENT + 3:   # rest → run
                    self._tested['rest'] = True
                    self._glow['rest']   = 48
                    self._sigbar         = 1.0

            # Decay per frame
            self._sigbar = max(0.0, self._sigbar - 0.022)
            for k in self._glow:
                self._glow[k] = max(0, self._glow[k] - 1)
            dot_tick = (dot_tick + 1) % 90

            # ── Draw ──────────────────────────────────────────────────────────
            self._draw_menu_scene()

            # Panel background
            panel = pygame.Rect(W // 2 - 410, 50, 820, 545)
            pygame.draw.rect(self.screen, (18, 20, 32), panel, border_radius=14)
            pygame.draw.rect(self.screen, (52, 58, 100), panel, 2, border_radius=14)

            cx = W // 2

            # Title
            t = self.font.render("EMG  CALIBRATION", True, (170, 205, 255))
            self.screen.blit(t, t.get_rect(center=(cx, 95)))

            # Connection status
            if self.emg_connected:
                dot_col   = (55, 220, 85)
                conn_text = "CONNECTED"
            else:
                dot_col   = (55, 220, 85) if (dot_tick // 22) % 2 == 0 else (25, 75, 35)
                n_dots    = (dot_tick // 22) % 4
                conn_text = "WAITING" + "." * n_dots

            pygame.draw.circle(self.screen, dot_col, (cx - 100, 138), 8)
            cs = self.font_sm.render(conn_text, True, dot_col)
            self.screen.blit(cs, (cx - 84, 131))

            # Signal activity bar
            bx, by, bw, bh = cx - 200, 165, 400, 14
            pygame.draw.rect(self.screen, (36, 40, 58), (bx, by, bw, bh), border_radius=4)
            fw = int(bw * self._sigbar)
            if fw > 2:
                r = min(255, 55 + int(self._sigbar * 170))
                g = min(255, 205 - int(self._sigbar * 50))
                b = 75
                pygame.draw.rect(self.screen, (r, g, b), (bx, by, fw, bh), border_radius=4)
            bar_lbl = self.font_sm.render("SIGNAL", True, (90, 98, 138))
            self.screen.blit(bar_lbl, (bx - 78, by))

            # Instructions
            instr = self.font_sm.render(
                "Perform each gesture to verify your sensor:", True, (150, 158, 195))
            self.screen.blit(instr, instr.get_rect(center=(cx, 200)))

            # Gesture tiles
            tiles = [
                ('rest',   'REST',   'Relax arm',    ( 55, 130, 215)),
                ('clench', 'CLENCH', 'Fist squeeze', (215,  90,  50)),
                ('wrist',  'WRIST',  'Wrist flex',   ( 55, 190,  80)),
            ]
            tw, th = 200, 165
            ty     = 225
            for i, (key, label, desc, col) in enumerate(tiles):
                tx    = cx - 310 + i * 220
                glow  = self._glow[key]
                ok    = self._tested[key]

                # Background: lit up when gesture just detected
                alpha = min(255, 55 + glow * 4)
                bg    = tuple(min(255, int(c * alpha / 255)) for c in col) if glow else (28, 30, 46)
                tr    = pygame.Rect(tx, ty, tw, th)
                pygame.draw.rect(self.screen, bg,                      tr, border_radius=10)
                pygame.draw.rect(self.screen, col if glow else (50, 55, 90), tr, 2, border_radius=10)

                lbl_s  = self.font_sm.render(label, True, (225, 228, 242))
                desc_s = self.font_sm.render(desc,  True, (130, 138, 168))
                self.screen.blit(lbl_s,  lbl_s.get_rect( center=(tx + tw // 2, ty + 32)))
                self.screen.blit(desc_s, desc_s.get_rect(center=(tx + tw // 2, ty + 62)))

                if ok:
                    ck = self.font.render("✓", True, (75, 230, 100))
                    self.screen.blit(ck, ck.get_rect(center=(tx + tw // 2, ty + 118)))
                else:
                    ws = self.font_sm.render("waiting...", True, (80, 86, 118))
                    self.screen.blit(ws, ws.get_rect(center=(tx + tw // 2, ty + 118)))

            # Status line below tiles
            n_tested = sum(self._tested.values())
            if not self.emg_connected:
                st = self.font_sm.render(
                    "Run the EMG inference engine to connect", True, (95, 100, 138))
            elif n_tested == 3:
                st = self.font_sm.render(
                    "All gestures verified!  Ready to play.", True, (75, 220, 100))
            else:
                st = self.font_sm.render(
                    f"{n_tested} / 3 gestures tested", True, (145, 150, 185))
            self.screen.blit(st, st.get_rect(center=(cx, 418)))

            # Tip: keyboard also works in EMG mode
            tip = self.font_sm.render(
                "Tip: SPACE / DOWN also work during gameplay", True, (75, 80, 110))
            self.screen.blit(tip, tip.get_rect(center=(cx, 447)))

            self._btn(start_btn, "START GAME",  (44, 105, 165), (65, 138, 212), self.font_sm)
            self._btn(back_btn,  "← BACK",      (55,  55,  78), (78,  78, 108), self.font_sm)

            enter_hint = self.font_sm.render("or press ENTER", True, (82, 88, 118))
            self.screen.blit(enter_hint, enter_hint.get_rect(center=(cx, H - 28)))

            self.clock.tick(FPS)
            pygame.display.update()

    # ── Scoreboard ────────────────────────────────────────────────────────────
    def show_scoreboard(self, highlight_score=None):
        scores   = load_scores()
        back_btn = pygame.Rect(W // 2 - 110, H - 78, 220, 44)

        # Find index of highlighted entry (first match)
        hi_idx = None
        if highlight_score is not None:
            for i, e in enumerate(scores):
                if e['score'] == int(highlight_score):
                    hi_idx = i
                    break

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == self.CLOUD_EVENT:
                    self._menu_clouds.add(
                        Cloud(self.cloud_img, W + 100, random.randint(50, 280)))
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                    return
                if self._clicked(back_btn, event):
                    return

            self._draw_menu_scene()

            # Panel
            panel = pygame.Rect(W // 2 - 370, 38, 740, H - 128)
            pygame.draw.rect(self.screen, (16, 18, 28), panel, border_radius=14)
            pygame.draw.rect(self.screen, (50, 56, 98),  panel, 2, border_radius=14)

            cx = W // 2
            tt = self.font.render("SCOREBOARD", True, (190, 195, 225))
            self.screen.blit(tt, tt.get_rect(center=(cx, 75)))

            if not scores:
                em = self.font_sm.render("No scores yet — go play!", True, (95, 100, 138))
                self.screen.blit(em, em.get_rect(center=(cx, 280)))
            else:
                # Column headers
                hy = 112
                for text, x in [("#",  panel.left + 28),
                                 ("MODE",  panel.left + 72),
                                 ("SCORE", panel.left + 188),
                                 ("DATE",  panel.left + 390)]:
                    self.screen.blit(
                        self.font_sm.render(text, True, (88, 95, 135)),
                        (x, hy))
                pygame.draw.line(
                    self.screen, (50, 56, 98),
                    (panel.left + 18, hy + 22), (panel.right - 18, hy + 22))

                RANK_COLS = {1: (255, 210, 50), 2: (195, 195, 210), 3: (200, 130, 70)}
                for rank, entry in enumerate(scores[:13], 1):
                    ey = hy + 28 + (rank - 1) * 36

                    # Row highlight for just-added score
                    if hi_idx is not None and (rank - 1) == hi_idx:
                        hr = pygame.Rect(panel.left + 10, ey - 3, panel.width - 20, 30)
                        pygame.draw.rect(self.screen, (40, 80, 120), hr, border_radius=5)

                    row_col = RANK_COLS.get(rank, (185, 188, 210))

                    # Rank
                    self.screen.blit(
                        self.font_sm.render(f"{rank:02d}", True, row_col),
                        (panel.left + 28, ey))

                    # Mode badge
                    mc  = EMG_COL if entry['mode'] == 'emg' else KB_COL
                    tag = "EMG"   if entry['mode'] == 'emg' else "KB"
                    br  = pygame.Rect(panel.left + 62, ey - 1, 52, 22)
                    pygame.draw.rect(self.screen, mc, br, border_radius=4)
                    ms  = self.font_sm.render(tag, True, (240, 240, 240))
                    self.screen.blit(ms, ms.get_rect(center=br.center))

                    # Score
                    self.screen.blit(
                        self.font_sm.render(f"{entry['score']:,}", True, row_col),
                        (panel.left + 188, ey))

                    # Date
                    self.screen.blit(
                        self.font_sm.render(entry.get('date', ''), True, (80, 88, 115)),
                        (panel.left + 390, ey))

            self._btn(back_btn, "← BACK", (52, 55, 80), (75, 78, 110), self.font_sm)

            self.clock.tick(FPS)
            pygame.display.update()

    # ── Game over overlay ─────────────────────────────────────────────────────
    def _show_game_over(self, score, hi):
        """Draw game over overlay. Returns 'restart' or 'menu'."""
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 490, 320
        panel  = pygame.Rect((W - pw) // 2, (H - ph) // 2 - 20, pw, ph)
        pygame.draw.rect(self.screen, (20, 22, 33),  panel, border_radius=14)
        pygame.draw.rect(self.screen, (62, 65, 102), panel, 2, border_radius=14)

        cx = W // 2
        go = self.font.render("GAME  OVER",                         True, (218, 72, 72))
        sc = self.font_sm.render(f"Score    {int(score):05d}",      True, (195, 198, 218))
        hi_s = self.font_sm.render(f"Best     {int(hi):05d}",       True, (252, 208, 52))
        self.screen.blit(go,  go.get_rect( center=(cx, panel.top + 62)))
        self.screen.blit(sc,  sc.get_rect( center=(cx, panel.top + 115)))
        self.screen.blit(hi_s, hi_s.get_rect(center=(cx, panel.top + 145)))

        rb = pygame.Rect(cx - 140, panel.top + 192, 280, 46)
        mb = pygame.Rect(cx - 140, panel.top + 252, 280, 38)
        self._btn(rb, "RESTART",       (44, 105, 165), (65, 138, 212), self.font_sm)
        self._btn(mb, "← MAIN MENU",   (52,  52,  78), (75,  75, 108), self.font_sm)

        ph2 = self.font_sm.render("or press SPACE to restart", True, (85, 90, 115))
        self.screen.blit(ph2, ph2.get_rect(center=(cx, panel.bottom + 22)))

        pygame.display.update()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    return 'restart'
                if self._clicked(rb, event):
                    return 'restart'
                if self._clicked(mb, event):
                    return 'menu'
                if event.type == pygame.USEREVENT + 1:   # EMG jump = restart
                    return 'restart'

    # ── Game loop ─────────────────────────────────────────────────────────────
    def run_game(self, mode):
        """Run one session (may restart multiple times). Returns last score."""
        game_speed        = 7.0
        player_score      = 0.0
        all_scores        = load_scores()
        high_score        = all_scores[0]['score'] if all_scores else 0
        game_over         = False
        flash_alpha       = 0
        last_sound_score  = 0
        particles         = []
        prev_jumping      = False
        ground_x          = 0
        _speed_lines      = [
            {'x': random.randint(0, W), 'y': random.randint(80, 320),
             'len': random.randint(30, 110)}
            for _ in range(22)
        ]

        cloud_group    = pygame.sprite.Group()
        obstacle_group = pygame.sprite.Group()
        dino_group     = pygame.sprite.GroupSingle()
        dinosaur       = Dino(200, DINO_GROUND)
        dino_group.add(dinosaur)

        obstacle_timer    = pygame.time.get_ticks()
        obstacle_spawn    = False
        obstacle_cooldown = 1000

        # ── Inner helpers ─────────────────────────────────────────────────────
        def draw_bg():
            self.screen.blit(self.sky_surf, (0, 0))
            factor = max(0.0, (game_speed - 13.0) / 9.0)
            if factor > 0:
                for ln in _speed_lines:
                    ln['x'] -= game_speed * 1.8
                    if ln['x'] + ln['len'] < 0:
                        ln['x']   = W + random.randint(0, 200)
                        ln['y']   = random.randint(80, 320)
                        ln['len'] = random.randint(30, 110)
                    s = pygame.Surface((ln['len'], 2), pygame.SRCALPHA)
                    s.fill((255, 255, 255, int(factor * 130)))
                    self.screen.blit(s, (int(ln['x']), ln['y']))
            pygame.draw.rect(self.screen, EARTH_COL,  (0, GROUND_Y + 18, W, H - GROUND_Y - 18))
            pygame.draw.rect(self.screen, EARTH_DARK, (0, GROUND_Y + 13, W, 6))

        def draw_ground():
            self.screen.blit(self.ground_img, (ground_x,     GROUND_Y))
            self.screen.blit(self.ground_img, (ground_x + W, GROUND_Y))

        def draw_score():
            sc = self.font.render(f"{int(player_score):05d}",     True, SCORE_COL)
            hi = self.font_sm.render(f"HI {int(high_score):05d}", True, HI_COL)
            # Mode badge — top left
            mc  = EMG_COL if mode == 'emg' else KB_COL
            tag = "EMG"   if mode == 'emg' else "KB"
            br  = pygame.Rect(14, 14, 52, 26)
            pygame.draw.rect(self.screen, mc, br, border_radius=5)
            ms  = self.font_sm.render(tag, True, (240, 240, 240))
            self.screen.blit(ms, ms.get_rect(center=br.center))
            # Score — top right
            sc_x = W - 20 - sc.get_width()
            self.screen.blit(hi, (sc_x - 14 - hi.get_width(), 18))
            self.screen.blit(sc, (sc_x, 14))

        def spawn_dust(cx, y):
            for _ in range(10):
                particles.append({
                    'x': cx + random.uniform(-20, 20), 'y': y,
                    'vx': random.uniform(-2.5, 2.5),   'vy': random.uniform(-4.0, -1.0),
                    'life': 1.0, 'size': random.randint(3, 8),
                })

        def draw_particles():
            alive = []
            for p in particles:
                p['life'] -= 0.055
                if p['life'] <= 0:
                    continue
                p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += 0.18
                sz = max(1, int(p['size'] * p['life']))
                s  = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*EARTH_COL, int(p['life'] * 210)), (sz, sz), sz)
                self.screen.blit(s, (int(p['x']) - sz, int(p['y']) - sz))
                alive.append(p)
            particles[:] = alive

        # ── Game loop ─────────────────────────────────────────────────────────
        while True:
            # Keyboard input (duck held)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_DOWN]:
                dinosaur.duck()
            elif dinosaur.ducking and mode == 'keyboard':
                dinosaur.unduck()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == self.CLOUD_EVENT:
                    cloud_group.add(
                        Cloud(self.cloud_img, W + 100, random.randint(50, 280)))

                # Jump (keyboard always works as fallback)
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP):
                    if not game_over and dinosaur.jump():
                        if self.jump_sfx:
                            self.jump_sfx.play()

                # EMG events (processed in both modes as fallback, primary in emg mode)
                if event.type == pygame.USEREVENT + 1:
                    if not game_over and dinosaur.jump():
                        if self.jump_sfx:
                            self.jump_sfx.play()
                if event.type == pygame.USEREVENT + 2:
                    dinosaur.duck()
                if event.type == pygame.USEREVENT + 3:
                    if mode == 'emg':
                        dinosaur.unduck()

            # Collision (use shrunken hitboxes to avoid phantom deaths from transparent padding)
            if (not game_over and
                    pygame.sprite.spritecollide(
                        dino_group.sprite, obstacle_group, False, _collide_hitbox)):
                game_over    = True
                high_score   = max(high_score, player_score)
                if self.death_sfx:
                    self.death_sfx.play()

            # Draw background
            draw_bg()

            if game_over:
                # Draw last frame state then overlay
                cloud_group.draw(self.screen)
                obstacle_group.draw(self.screen)
                dino_group.draw(self.screen)
                draw_ground()
                draw_score()
                pygame.display.update()

                save_score(player_score, mode)
                result = self._show_game_over(player_score, high_score)

                if result == 'menu':
                    return player_score

                # Restart
                game_speed        = 7.0
                player_score      = 0.0
                game_over         = False
                flash_alpha       = 0
                last_sound_score  = 0
                particles.clear()
                cloud_group.empty()
                obstacle_group.empty()
                dinosaur.rect.centery = DINO_GROUND
                dinosaur.ducking      = False
                dinosaur.is_jumping   = False
                dinosaur.velocity_y   = 0
                prev_jumping          = False
                obstacle_timer        = pygame.time.get_ticks()
                continue

            # Game logic
            game_speed   += 0.0015
            player_score += 0.1

            score_int = int(player_score)
            if score_int > 0 and score_int % 100 == 0 and score_int != last_sound_score:
                last_sound_score = score_int
                if self.points_sfx:
                    self.points_sfx.play()
                flash_alpha = 200

            if pygame.time.get_ticks() - obstacle_timer >= obstacle_cooldown:
                obstacle_spawn = True
            if obstacle_spawn:
                r = random.randint(1, 50)
                if r <= 6:
                    obstacle_group.add(Cactus(W, 340, game_speed))
                    obstacle_timer = pygame.time.get_ticks()
                    obstacle_spawn = False
                elif r <= 9:
                    obstacle_group.add(Ptero(game_speed))
                    obstacle_timer = pygame.time.get_ticks()
                    obstacle_spawn = False

            ground_x -= game_speed
            if ground_x <= -W:
                ground_x = 0

            # Draw sprites
            cloud_group.update(max(1.0, game_speed * 0.14))
            cloud_group.draw(self.screen)

            for obs in obstacle_group:
                obs.speed = game_speed
            obstacle_group.update()
            obstacle_group.draw(self.screen)

            dino_group.update()
            dino_group.draw(self.screen)

            draw_ground()

            # Landing dust
            now_jumping = dinosaur.is_jumping
            if prev_jumping and not now_jumping:
                spawn_dust(dinosaur.rect.centerx, dinosaur.rect.bottom - 8)
            prev_jumping = now_jumping

            draw_particles()

            if flash_alpha > 0:
                fs = pygame.Surface((W, H), pygame.SRCALPHA)
                fs.fill((255, 255, 255, int(flash_alpha)))
                self.screen.blit(fs, (0, 0))
                flash_alpha = max(0, flash_alpha - 14)

            draw_score()

            self.clock.tick(FPS)
            pygame.display.update()

    # ── Main entry ────────────────────────────────────────────────────────────
    def run(self):
        while True:
            action = self.show_main_menu()

            if action == 'scoreboard':
                self.show_scoreboard()
                continue

            mode = action   # 'emg' or 'keyboard'

            if mode == 'emg':
                self.start_emg()
                if self.show_calibration() == 'back':
                    continue

            final_score = self.run_game(mode)
            self.show_scoreboard(highlight_score=int(final_score))


# ── Sprite classes ────────────────────────────────────────────────────────────
class Cloud(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect  = self.image.get_rect(center=(x, y))

    def update(self, speed=1.0):
        self.rect.x -= speed
        if self.rect.right < 0:
            self.kill()


class Dino(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.run_sprites = [
            pygame.transform.scale(pygame.image.load("assets/Dino1.png"),        (80, 100)),
            pygame.transform.scale(pygame.image.load("assets/Dino2.png"),        (80, 100)),
        ]
        self.duck_sprites = [
            pygame.transform.scale(pygame.image.load("assets/DinoDucking1.png"), (110, 60)),
            pygame.transform.scale(pygame.image.load("assets/DinoDucking2.png"), (110, 60)),
        ]
        self.image      = self.run_sprites[0]
        self.rect       = self.image.get_rect(center=(x, y))
        self.velocity_y = 0
        self.jump_str   = -22
        self.gravity    = 1
        self.ground_y   = y
        self.ducking    = False
        self.is_jumping = False
        self._frame     = 0.0

    def jump(self):
        if self.rect.centery >= self.ground_y and not self.ducking and not self.is_jumping:
            self.is_jumping = True
            self.velocity_y = self.jump_str
            return True
        return False

    def duck(self):
        if not self.ducking and not self.is_jumping:
            self.ducking = True
            self.rect.centery = self.ground_y + 20

    def unduck(self):
        if self.ducking:
            self.ducking = False
            self.rect.centery = self.ground_y

    def _physics(self):
        if self.is_jumping or self.rect.centery < self.ground_y:
            self.velocity_y   += self.gravity
            self.rect.centery += self.velocity_y
            if self.rect.centery >= self.ground_y:
                self.rect.centery = self.ground_y
                self.velocity_y   = 0
                self.is_jumping   = False

    @property
    def hitbox(self):
        # Shrink to roughly the visible body, ignoring transparent edges
        if self.ducking:
            return self.rect.inflate(-38, -18)   # 110x60 → 72x42
        return self.rect.inflate(-24, -30)        # 80x100 → 56x70

    def _animate(self):
        self._frame = (self._frame + 0.05) % 2
        self.image  = (self.duck_sprites if self.ducking else self.run_sprites)[int(self._frame)]

    def update(self):
        self._animate()
        self._physics()


class Cactus(pygame.sprite.Sprite):
    _cache = None

    def __init__(self, x, y, speed):
        super().__init__()
        if Cactus._cache is None:
            Cactus._cache = [
                pygame.transform.scale(
                    pygame.image.load(f"assets/cacti/cactus{i}.png"), (100, 100))
                for i in range(1, 7)
            ]
        self.image = random.choice(Cactus._cache)
        self.rect  = self.image.get_rect(center=(x, y))
        self.speed = speed

    @property
    def hitbox(self):
        return self.rect.inflate(-40, -8)   # 100x100 → 60x92 (cactus trunk is narrow)

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


class Ptero(pygame.sprite.Sprite):
    _cache = None

    def __init__(self, speed):
        super().__init__()
        if Ptero._cache is None:
            Ptero._cache = [
                pygame.transform.scale(pygame.image.load("assets/Ptero1.png"), (84, 62)),
                pygame.transform.scale(pygame.image.load("assets/Ptero2.png"), (84, 62)),
            ]
        self._frame = 0.0
        self.image  = Ptero._cache[0]
        self.rect   = self.image.get_rect(center=(1300, random.choice([270, 295, 340])))
        self.speed  = speed

    @property
    def hitbox(self):
        return self.rect.inflate(-22, -16)   # 84x62 → 62x46

    def update(self):
        self._frame = (self._frame + 0.025) % 2
        self.image  = Ptero._cache[int(self._frame)]
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


def _collide_hitbox(a, b):
    """Collision using each sprite's shrunken hitbox instead of the full image rect."""
    return a.hitbox.colliderect(b.hitbox)


if __name__ == '__main__':
    app = App()
    app.run()
