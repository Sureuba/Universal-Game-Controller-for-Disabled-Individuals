# dino_game.py - Full game with EMG socket control
import pygame
import sys
import random
import socket
import threading

class DinoGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Dino Game - EMG Control")
        self.clock = pygame.time.Clock()
        
        # Load custom font
        try:
            self.game_font = pygame.font.Font("assets/PressStart2P-Regular.ttf", 20)
        except:
            self.game_font = pygame.font.Font(None, 24)

        self.game_speed = 7
        self.player_score = 0
        self.game_over = False

        # Load and scale ground
        self.ground = pygame.image.load("assets/ground.png")
        self.ground = pygame.transform.scale(self.ground, (1280, 20))
        self.ground_x = 0

        # Load and scale cloud
        self.cloud = pygame.image.load("assets/cloud.png")
        self.cloud = pygame.transform.scale(self.cloud, (200, 80))
        
        # Sprite groups
        self.cloud_group = pygame.sprite.Group()
        self.obstacle_group = pygame.sprite.Group()
        self.dino_group = pygame.sprite.GroupSingle()

        self.dinosaur = Dino(400, 360)
        self.dino_group.add(self.dinosaur)

        # Load sounds
        try:
            self.death_sfx = pygame.mixer.Sound("assets/sfx/lose.mp3")
            self.points_sfx = pygame.mixer.Sound("assets/sfx/100points.mp3")
            self.jump_sfx = pygame.mixer.Sound("assets/sfx/jump.mp3")
        except:
            print("[WARNING] Could not load sound files")
            self.death_sfx = None
            self.points_sfx = None
            self.jump_sfx = None

        # Events
        self.CLOUD_EVENT = pygame.USEREVENT
        pygame.time.set_timer(self.CLOUD_EVENT, 3000)
        
        # Obstacle spawning
        self.obstacle_timer = 0
        self.obstacle_spawn = False
        self.obstacle_cooldown = 1000  # ms
        
        # Socket server for EMG control
        self.socket_thread = threading.Thread(target=self.socket_server, daemon=True)
        self.socket_thread.start()

    def socket_server(self):
        """Listen for EMG commands via socket"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('127.0.0.1', 9999))
            server_socket.listen(1)
            print("[SOCKET] Waiting for EMG connection on port 9999...")
            
            conn, addr = server_socket.accept()
            print(f"[SOCKET] EMG connected from {addr}")
            
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    
                    command = data.decode().strip()
                    print(f"[EMG COMMAND] {command}")
                    
                    # Post pygame events based on command
                    if command == "jump":
                        pygame.event.post(pygame.event.Event(pygame.USEREVENT + 1))
                    elif command == "duck":
                        pygame.event.post(pygame.event.Event(pygame.USEREVENT + 2))
                    elif command == "run":
                        pygame.event.post(pygame.event.Event(pygame.USEREVENT + 3))
                    else:
                        print(f"[SOCKET] Unknown command: {command}")
                        
                except Exception as e:
                    print(f"[SOCKET] Error receiving data: {e}")
                    break
            
            conn.close()
            print("[SOCKET] EMG disconnected")
        except Exception as e:
            print(f"[SOCKET] Server error: {e}")
        finally:
            server_socket.close()

    def end_game(self):
        """Display game over screen"""
        self.screen.fill("white")
        
        game_over_text = self.game_font.render("Game Over!", True, "black")
        game_over_rect = game_over_text.get_rect(center=(640, 300))
        
        score_text = self.game_font.render(f"Score: {int(self.player_score)}", True, "black")
        score_rect = score_text.get_rect(center=(640, 350))

        restart_button = pygame.Rect(540, 400, 200, 50)
        pygame.draw.rect(self.screen, "gray", restart_button)
        restart_text = self.game_font.render("Restart", True, "black")
        restart_text_rect = restart_text.get_rect(center=restart_button.center)
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(restart_text, restart_text_rect)
        
        pygame.display.update()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and restart_button.collidepoint(event.pos):
                    self.reset_game()
                    waiting = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.reset_game()
                    waiting = False

    def reset_game(self):
        """Reset game state"""
        self.player_score = 0
        self.game_speed = 7
        self.cloud_group.empty()
        self.obstacle_group.empty()
        self.dinosaur.rect.centery = 360
        self.dinosaur.ducking = False
        self.game_over = False
        self.obstacle_timer = pygame.time.get_ticks()

    def run(self):
        """Main game loop"""
        print("[GAME] Dino game started!")
        print("[GAME] Controls:")
        print("  Keyboard: SPACE/UP=jump, DOWN=duck")
        print("  EMG: Waiting for muscle gestures...")
        
        while True:
            # Keyboard input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_DOWN]:
                self.dinosaur.duck()
            else:
                if self.dinosaur.ducking:
                    self.dinosaur.unduck()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == self.CLOUD_EVENT:
                    current_cloud_y = random.randint(50, 300)
                    current_cloud = Cloud(self.cloud, 1380, current_cloud_y)
                    self.cloud_group.add(current_cloud)
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        self.dinosaur.jump()
                        if self.jump_sfx:
                            self.jump_sfx.play()
                        if self.game_over:
                            self.reset_game()
                
                # EMG control events
                if event.type == pygame.USEREVENT + 1:  # Jump command from EMG
                    self.dinosaur.jump()
                    if self.jump_sfx:
                        self.jump_sfx.play()
                    
                if event.type == pygame.USEREVENT + 2:  # Duck command from EMG
                    self.dinosaur.duck()
                    
                if event.type == pygame.USEREVENT + 3:  # Run command from EMG
                    self.dinosaur.unduck()
            
            # Clear screen
            self.screen.fill("white")
            
            # Check collision
            if pygame.sprite.spritecollide(self.dino_group.sprite, self.obstacle_group, False):
                if not self.game_over:
                    self.game_over = True
                    if self.death_sfx:
                        self.death_sfx.play()
            
            if self.game_over:
                self.end_game()
            else:
                # Game logic
                self.game_speed += 0.0015
                
                # Score and sound
                if round(self.player_score, 1) % 100 == 0 and int(self.player_score) > 0:
                    if self.points_sfx:
                        self.points_sfx.play()
                
                # Spawn obstacles
                if pygame.time.get_ticks() - self.obstacle_timer >= self.obstacle_cooldown:
                    self.obstacle_spawn = True
                
                if self.obstacle_spawn:
                    obstacle_random = random.randint(1, 50)
                    if obstacle_random in range(1, 7):  # Cactus
                        new_obstacle = Cactus(1280, 340)
                        self.obstacle_group.add(new_obstacle)
                        self.obstacle_timer = pygame.time.get_ticks()
                        self.obstacle_spawn = False
                    elif obstacle_random in range(7, 10):  # Ptero
                        new_obstacle = Ptero()
                        self.obstacle_group.add(new_obstacle)
                        self.obstacle_timer = pygame.time.get_ticks()
                        self.obstacle_spawn = False
                
                # Update score
                self.player_score += 0.1
                player_score_surface = self.game_font.render(str(int(self.player_score)), True, "black")
                self.screen.blit(player_score_surface, (1150, 10))
                
                # Update and draw sprites
                self.cloud_group.update()
                self.cloud_group.draw(self.screen)
                
                self.obstacle_group.update()
                self.obstacle_group.draw(self.screen)
                
                self.dino_group.update()
                self.dino_group.draw(self.screen)
                
                # Draw ground
                self.ground_x -= self.game_speed
                self.screen.blit(self.ground, (self.ground_x, 360))
                self.screen.blit(self.ground, (self.ground_x + 1280, 360))
                
                if self.ground_x <= -1280:
                    self.ground_x = 0
            
            self.clock.tick(120)
            pygame.display.update()


class Cloud(pygame.sprite.Sprite):
    """Cloud sprite"""
    def __init__(self, image, x_pos, y_pos):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x_pos, y_pos))
    
    def update(self):
        self.rect.x -= 1
        if self.rect.right < 0:
            self.kill()

class Dino(pygame.sprite.Sprite):
    """Dinosaur player sprite"""
    def __init__(self, x_pos, y_pos):
        super().__init__()
        self.running_sprites = [
            pygame.transform.scale(pygame.image.load("assets/Dino1.png"), (80, 100)),
            pygame.transform.scale(pygame.image.load("assets/Dino2.png"), (80, 100))
        ]
        self.ducking_sprites = [
            pygame.transform.scale(pygame.image.load("assets/DinoDucking1.png"), (110, 60)),
            pygame.transform.scale(pygame.image.load("assets/DinoDucking2.png"), (110, 60))
        ]
        self.image = self.running_sprites[0]
        self.rect = self.image.get_rect(center=(x_pos, y_pos))
        
        # Physics-based jump
        self.velocity_y = 100          # Current vertical velocity
        self.jump_strength = -22     # Initial upward force (negative = up)
        self.gravity = 1           # Gravity acceleration
        self.ground_y = 360          # Ground level
        
        self.ducking = False
        self.current_image = 0
        self.is_jumping = False

    def jump(self):
        """Start jump by giving upward velocity"""
        if self.rect.centery >= self.ground_y and not self.ducking and not self.is_jumping:
            self.is_jumping = True
            self.velocity_y = self.jump_strength  # Give initial upward velocity

    def duck(self):
        if not self.ducking and not self.is_jumping:
            self.ducking = True
            self.rect.centery = 380

    def unduck(self):
        if self.ducking:
            self.ducking = False
            self.rect.centery = self.ground_y

    def apply_physics(self):
        """Apply velocity and gravity each frame"""
        if self.is_jumping or self.rect.centery < self.ground_y:
            # Apply gravity (increases velocity downward each frame)
            self.velocity_y += self.gravity
            
            # Move by current velocity
            self.rect.centery += self.velocity_y
            
            # Check if landed
            if self.rect.centery >= self.ground_y:
                self.rect.centery = self.ground_y
                self.velocity_y = 0
                self.is_jumping = False

    def update(self):
        self.animate()
        self.apply_physics()  # Changed from apply_gravity

    def animate(self):
        self.current_image += 0.05
        if self.current_image >= 2:
            self.current_image = 0
        
        if self.ducking:
            self.image = self.ducking_sprites[int(self.current_image)]
        else:
            self.image = self.running_sprites[int(self.current_image)]


class Cactus(pygame.sprite.Sprite):
    """Cactus obstacle"""
    def __init__(self, x_pos, y_pos):
        super().__init__()
        self.sprites = []
        for i in range(1, 7):
            sprite = pygame.transform.scale(
                pygame.image.load(f"assets/cacti/cactus{i}.png"), (100, 100)
            )
            self.sprites.append(sprite)
        
        self.image = random.choice(self.sprites)
        self.rect = self.image.get_rect(center=(x_pos, y_pos))

    def update(self):
        global game_speed
        self.rect.x -= 7  # Use game speed from game instance
        if self.rect.right < 0:
            self.kill()


class Ptero(pygame.sprite.Sprite):
    """Flying pterodactyl obstacle"""
    def __init__(self):
        super().__init__()
        self.sprites = [
            pygame.transform.scale(pygame.image.load("assets/Ptero1.png"), (84, 62)),
            pygame.transform.scale(pygame.image.load("assets/Ptero2.png"), (84, 62))
        ]
        self.current_image = 0
        self.image = self.sprites[self.current_image]
        self.rect = self.image.get_rect(center=(1300, random.choice([280, 295, 350])))

    def update(self):
        self.animate()
        self.rect.x -= 7
        if self.rect.right < 0:
            self.kill()

    def animate(self):
        self.current_image += 0.025
        if self.current_image >= 2:
            self.current_image = 0
        self.image = self.sprites[int(self.current_image)]


if __name__ == '__main__':
    game = DinoGame()
    game.run()


