# emg_test_game.py - EMG sensor test mode (no obstacles)
# Run this to verify your MyoWare sensor is working before playing the real game.
import pygame
import sys
import random
import socket
import threading
from datetime import datetime

W, H        = 1280, 720
GROUND_Y    = 360
DINO_GROUND = 360
FPS         = 120

# ── Colours (same as main game) ───────────────────────────────────────────────
SKY_TOP    = (108, 189, 237)
SKY_BOT    = (215, 238, 252)
EARTH_COL  = (160, 120,  68)
EARTH_DARK = (115,  82,  38)

GESTURE_COLS = {
    'clench': (220,  90,  50),   # orange-red
    'wrist':  ( 55, 190,  80),   # green
    'rest':   ( 55, 130, 215),   # blue
}


def _make_sky(w, h):
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
    return surf


# ── Dino sprite (same as main game) ──────────────────────────────────────────
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

    def update(self):
        self._frame = (self._frame + 0.05) % 2
        self.image  = (self.duck_sprites if self.ducking else self.run_sprites)[int(self._frame)]
        if self.is_jumping or self.rect.centery < self.ground_y:
            self.velocity_y   += self.gravity
            self.rect.centery += self.velocity_y
            if self.rect.centery >= self.ground_y:
                self.rect.centery = self.ground_y
                self.velocity_y   = 0
                self.is_jumping   = False


# ── Cloud sprite ──────────────────────────────────────────────────────────────
class Cloud(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect  = self.image.get_rect(center=(x, y))

    def update(self, speed=0.8):
        self.rect.x -= speed
        if self.rect.right < 0:
            self.kill()


# ── Test app ──────────────────────────────────────────────────────────────────
class EMGTestApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("EMG Test Mode — No Obstacles")
        self.clock  = pygame.time.Clock()

        try:
            self.font    = pygame.font.Font("assets/PressStart2P-Regular.ttf", 14)
            self.font_sm = pygame.font.Font("assets/PressStart2P-Regular.ttf", 10)
        except Exception:
            self.font    = pygame.font.Font(None, 22)
            self.font_sm = pygame.font.Font(None, 18)

        self.sky_surf   = _make_sky(W, GROUND_Y + 24)
        self.ground_img = pygame.transform.scale(
            pygame.image.load("assets/ground.png"), (W, 20))
        self.cloud_img  = pygame.transform.scale(
            pygame.image.load("assets/cloud.png"), (200, 80))

        try:
            self.jump_sfx = pygame.mixer.Sound("assets/sfx/jump.mp3")
        except Exception:
            self.jump_sfx = None

        self.CLOUD_EVENT = pygame.USEREVENT
        pygame.time.set_timer(self.CLOUD_EVENT, 3000)

        # EMG state
        self.emg_connected  = False
        self.last_gesture   = None    # 'clench' | 'wrist' | 'rest'
        self.last_command   = None    # 'jump' | 'duck' | 'run'
        self.gesture_flash  = 0       # countdown frames for the glow
        self.gesture_log    = []      # list of (gesture, command, time_str)

        threading.Thread(target=self._socket_server, daemon=True).start()

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

    def _log_gesture(self, gesture, command):
        ts = datetime.now().strftime("%H:%M:%S")
        self.gesture_log.append((gesture, command, ts))
        if len(self.gesture_log) > 10:
            self.gesture_log.pop(0)
        self.last_gesture  = gesture
        self.last_command  = command
        self.gesture_flash = 55

    def _draw_hud(self):
        """Right-side panel showing connection status, last gesture, and log."""
        px, py, pw, ph = W - 310, 20, 290, H - 40
        panel = pygame.Rect(px, py, pw, ph)
        s = pygame.Surface((pw, ph), pygame.SRCALPHA)
        s.fill((15, 17, 28, 210))
        self.screen.blit(s, (px, py))
        pygame.draw.rect(self.screen, (50, 55, 95), panel, 1, border_radius=10)

        cx = px + pw // 2
        y  = py + 18

        # Title
        t = self.font_sm.render("EMG TEST MODE", True, (160, 168, 215))
        self.screen.blit(t, t.get_rect(center=(cx, y)))
        y += 28

        # Divider
        pygame.draw.line(self.screen, (45, 50, 88), (px + 10, y), (px + pw - 10, y))
        y += 14

        # Connection status
        dot_col = (55, 220, 80) if self.emg_connected else (180, 60, 60)
        pygame.draw.circle(self.screen, dot_col, (px + 20, y + 7), 7)
        status = "CONNECTED" if self.emg_connected else "NOT CONNECTED"
        st = self.font_sm.render(status, True, dot_col)
        self.screen.blit(st, (px + 34, y))
        y += 30

        # Divider
        pygame.draw.line(self.screen, (45, 50, 88), (px + 10, y), (px + pw - 10, y))
        y += 14

        # Last gesture display
        hdr = self.font_sm.render("LAST GESTURE", True, (90, 96, 135))
        self.screen.blit(hdr, (px + 12, y))
        y += 22

        if self.last_gesture:
            col   = GESTURE_COLS.get(self.last_gesture, (200, 200, 200))
            alpha = min(255, self.gesture_flash * 5)
            # Glowing background rect
            gr = pygame.Rect(px + 10, y, pw - 20, 52)
            gs = pygame.Surface((gr.width, gr.height), pygame.SRCALPHA)
            gs.fill((*col, max(30, alpha // 3)))
            self.screen.blit(gs, gr.topleft)
            pygame.draw.rect(self.screen, (*col, alpha), gr, 2, border_radius=6)

            gname = self.font.render(self.last_gesture.upper(), True, col)
            gcmd  = self.font_sm.render(f"→  {self.last_command}", True, (200, 205, 225))
            self.screen.blit(gname, gname.get_rect(center=(cx, y + 18)))
            self.screen.blit(gcmd,  gcmd.get_rect( center=(cx, y + 38)))
        else:
            none_s = self.font_sm.render("waiting...", True, (70, 75, 108))
            self.screen.blit(none_s, none_s.get_rect(center=(cx, y + 18)))
        y += 62

        # Divider
        pygame.draw.line(self.screen, (45, 50, 88), (px + 10, y), (px + pw - 10, y))
        y += 14

        # Gesture log
        lhdr = self.font_sm.render("GESTURE LOG", True, (90, 96, 135))
        self.screen.blit(lhdr, (px + 12, y))
        y += 22

        for i, (gest, cmd, ts) in enumerate(reversed(self.gesture_log)):
            if y + 22 > py + ph - 10:
                break
            col   = GESTURE_COLS.get(gest, (180, 180, 180))
            alpha = max(80, 255 - i * 22)
            faded = tuple(int(c * alpha / 255) for c in col)
            row   = self.font_sm.render(f"{gest:<8}  {cmd:<5}", True, faded)
            ts_s  = self.font_sm.render(ts, True, (55, 60, 90))
            self.screen.blit(row,  (px + 12, y))
            self.screen.blit(ts_s, (px + pw - 10 - ts_s.get_width(), y))
            y += 20

        # Controls hint at bottom
        hint_y = py + ph - 42
        pygame.draw.line(self.screen, (45, 50, 88),
                         (px + 10, hint_y - 8), (px + pw - 10, hint_y - 8))
        h1 = self.font_sm.render("SPACE = jump   DOWN = duck", True, (65, 70, 105))
        h2 = self.font_sm.render("ESC = quit", True, (65, 70, 105))
        self.screen.blit(h1, h1.get_rect(center=(cx, hint_y)))
        self.screen.blit(h2, h2.get_rect(center=(cx, hint_y + 18)))

    def _draw_top_banner(self):
        """Small banner at the top-left explaining this is test mode."""
        b = self.font_sm.render(
            "TEST MODE  —  no obstacles  —  connect EMG and flex!", True, (55, 60, 95))
        self.screen.blit(b, (16, 14))

    def run(self):
        print("[TEST] EMG test mode started")
        print("[TEST] SPACE=jump  DOWN=duck  ESC=quit")
        print("[TEST] Waiting for EMG inference engine on port 9999...")

        dino        = Dino(260, DINO_GROUND)
        cloud_group = pygame.sprite.Group()
        ground_x    = 0

        while True:
            # Keyboard duck (held)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_DOWN]:
                dino.duck()
            elif dino.ducking:
                dino.unduck()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key in (pygame.K_SPACE, pygame.K_UP):
                        if dino.jump() and self.jump_sfx:
                            self.jump_sfx.play()

                if event.type == self.CLOUD_EVENT:
                    cloud_group.add(Cloud(self.cloud_img, W + 100, random.randint(50, 280)))

                # EMG events
                if event.type == pygame.USEREVENT + 1:   # clench → jump
                    if dino.jump() and self.jump_sfx:
                        self.jump_sfx.play()
                    self._log_gesture('clench', 'jump')

                if event.type == pygame.USEREVENT + 2:   # wrist → duck
                    dino.duck()
                    self._log_gesture('wrist', 'duck')

                if event.type == pygame.USEREVENT + 3:   # rest → run
                    dino.unduck()
                    self._log_gesture('rest', 'run')

            # Decay flash
            self.gesture_flash = max(0, self.gesture_flash - 1)

            # ── Draw ──────────────────────────────────────────────────────────
            # Sky
            self.screen.blit(self.sky_surf, (0, 0))
            # Earth
            pygame.draw.rect(self.screen, EARTH_COL,  (0, GROUND_Y + 18, W, H - GROUND_Y - 18))
            pygame.draw.rect(self.screen, EARTH_DARK, (0, GROUND_Y + 13, W, 6))

            # Clouds
            cloud_group.update(0.8)
            cloud_group.draw(self.screen)

            # Dino
            dino.update()
            self.screen.blit(dino.image, dino.rect)

            # Scrolling ground strip (on top of dino feet)
            ground_x -= 4
            if ground_x <= -W:
                ground_x = 0
            self.screen.blit(self.ground_img, (ground_x,     GROUND_Y))
            self.screen.blit(self.ground_img, (ground_x + W, GROUND_Y))

            # HUD
            self._draw_hud()
            self._draw_top_banner()

            self.clock.tick(FPS)
            pygame.display.update()


if __name__ == '__main__':
    app = EMGTestApp()
    app.run()
