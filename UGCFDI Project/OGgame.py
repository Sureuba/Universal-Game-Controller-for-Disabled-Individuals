import pygame
import sys
import random

class DinoGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Dino Game")
        self.clock = pygame.time.Clock()
        self.game_font = pygame.font.Font(None, 24)

        self.game_speed = 7
        self.player_score = 0
        self.game_over = False

        self.ground = pygame.image.load("assets/ground.png")
        self.ground = pygame.transform.scale(self.ground, (1280, 20))
        self.ground_x = 0

        self.cloud = pygame.image.load("assets/cloud.png")
        self.cloud = pygame.transform.scale(self.cloud, (200, 80))
        
        self.cloud_group = pygame.sprite.Group()
        self.dino_group = pygame.sprite.GroupSingle()

        self.dinosaur = Dino(50, 360)
        self.dino_group.add(self.dinosaur)

        self.death_sfx = pygame.mixer.Sound("assets/sfx/lose.mp3")
        self.points_sfx = pygame.mixer.Sound("assets/sfx/100points.mp3")
        self.jump_sfx = pygame.mixer.Sound("assets/sfx/jump.mp3")

        self.CLOUD_EVENT = pygame.USEREVENT
        pygame.time.set_timer(self.CLOUD_EVENT, 3000)

    def end_game(self):
        self.screen.fill("white")
        game_over_text = self.game_font.render("Game Over!", True, "black")
        score_text = self.game_font.render(f"Score: {int(self.player_score)}", True, "black")

        restart_button = pygame.Rect(540, 380, 200, 50)
        pygame.draw.rect(self.screen, "gray", restart_button)
        restart_text = self.game_font.render("Restart", True, "black")
        
        self.screen.blit(game_over_text, (640, 300))
        self.screen.blit(score_text, (640, 340))
        self.screen.blit(restart_text, restart_button.topleft)
        
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

    def reset_game(self):
        self.player_score = 0
        self.game_speed = 7
        self.cloud_group.empty()
        self.dinosaur.rect.centery = 360
        self.game_over = False

    def run(self):
        while True:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_DOWN]:
                self.dinosaur.duck()
            else:
                if self.dinosaur.ducking:
                    self.dinosaur.unduck()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == self.CLOUD_EVENT:
                    current_cloud = Cloud(self.cloud, 1380, random.randint(50, 300))
                    self.cloud_group.add(current_cloud)
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_SPACE or event.key == pygame.K_UP):
                    self.dinosaur.jump()
                    if self.game_over:
                        self.reset_game()
            
            self.screen.fill("white")
            
            if self.game_over:
                self.end_game()
            else:
                self.game_speed += 0.0015
                if round(self.player_score, 1) % 100 == 0 and int(self.player_score) > 0:
                    self.points_sfx.play()
                
                self.player_score += 0.1
                score_surface = self.game_font.render(str(int(self.player_score)), True, "black")
                self.screen.blit(score_surface, (1150, 10))
                
                self.cloud_group.update()
                self.cloud_group.draw(self.screen)
                
                self.dino_group.update()
                self.dino_group.draw(self.screen)
                
                self.ground_x -= self.game_speed
                self.screen.blit(self.ground, (self.ground_x, 360))
                self.screen.blit(self.ground, (self.ground_x + 1280, 360))
                
                if self.ground_x <= -1280:
                    self.ground_x = 0
            
            self.clock.tick(120)
            pygame.display.update()

# Classes for Cloud and Dino

class Cloud(pygame.sprite.Sprite):
    def __init__(self, image, x_pos, y_pos):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x_pos, y_pos))
    
    def update(self):
        self.rect.x -= 1

class Dino(pygame.sprite.Sprite):
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
        self.velocity = 50
        self.gravity = 4.5
        self.ducking = False
        self.current_image = 0

    def jump(self):
        if self.rect.centery >= 360:
            self.rect.centery -= self.velocity

    def duck(self):
        self.ducking = True
        self.rect.centery = 380

    def unduck(self):
        self.ducking = False
        self.rect.centery = 360

    def apply_gravity(self):
        if self.rect.centery < 360:
            self.rect.centery += self.gravity

    def update(self):
        self.animate()
        self.apply_gravity()

    def animate(self):
        self.current_image += 0.05
        if self.current_image >= 2:
            self.current_image = 0
        self.image = self.ducking_sprites[int(self.current_image)] if self.ducking else self.running_sprites[int(self.current_image)]

