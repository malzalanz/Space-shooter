import pygame
import os
import time
import random

pygame.font.init()

WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space shooter 420803")

# spaceships
RED_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_red.png")), (int(WIDTH * 0.15), int(HEIGHT * 0.15)))
YELLOW_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_yellow.png")), (int(WIDTH * 0.15), int(HEIGHT * 0.15)))
GREEN_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_green.png")), (int(WIDTH * 0.15), int(HEIGHT * 0.15)))

BLUE_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_blue.png")), (int(WIDTH * 0.2), int(HEIGHT * 0.2)))

# lasers
RED_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_red.png")), (int(WIDTH * 0.1), int(HEIGHT * 0.1)))
YELLOW_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_yellow.png")), (int(WIDTH * 0.1), int(HEIGHT * 0.1)))
GREEN_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_green.png")), (int(WIDTH * 0.1), int(HEIGHT * 0.1)))

BLUE_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_blue.png")), (int(WIDTH * 0.12), int(HEIGHT * 0.12)))

# background
BG = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "space_background.png")), (WIDTH, HEIGHT))

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (self.y <= height)

    def collision(self, obj):
        if isinstance(obj, Ship):
            offset_x = obj.x - self.x
            offset_y = obj.y - self.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        return False

class Ship:
    COOLDOWN = 25  # ile ms miedzy kolejnymi strzałami

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 30, self.y - 10, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = BLUE_SPACE_SHIP
        self.laser_img = BLUE_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.score = 0

    def move_lasers(self, vel, objs):
        global score
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if isinstance(obj, Enemy) and laser.collision(obj):
                        objs.remove(obj)
                        self.lasers.remove(laser)
                        score += 2
                    elif laser.collision(obj) and isinstance(obj, Enemy):
                        self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height() - 10, self.ship_img.get_width(), 7))
        pygame.draw.rect(window, (0, 255, 0),
                         (self.x, self.y + self.ship_img.get_height() - 10,
                          self.ship_img.get_width() * (self.health / self.max_health), 7))

class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER),
        "yellow": (YELLOW_SPACE_SHIP, YELLOW_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 20, self.y + 35, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def collision(self, obj):
        if isinstance(obj, Player):
            offset_x = obj.x - self.x
            offset_y = obj.y - self.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        return False

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None

def main():
    global score
    run = True
    pygame.font.init()
    FPS = 60
    level = 0
    lives = 3
    score = 0
    main_font = pygame.font.SysFont("comicsans", 30)
    lost_font = pygame.font.SysFont("comicsans", 40)

    enemies = []
    wave_length = 5
    enemy_vel = 1

    player_vel = 5
    laser_vel = 7

    player = Player(300, 600)
    
    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def end_game_screen():
        WIN.blit(BG, (0, 0))
        end_label = lost_font.render(f"You lost. Your score: {score}", 1, (255, 255, 255))
        WIN.blit(end_label, (WIDTH / 2 - end_label.get_width() / 2, 350))
        pygame.display.update()
        pygame.time.delay(3000)
        run = False
    
    def redraw_window():
        WIN.blit(BG, (0, 0))

        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))
        score_label = main_font.render(f"Score: {score}", 1, (255, 255, 255))

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        WIN.blit(score_label, (WIDTH / 2 - score_label.get_width() / 2, 10))

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS * 3:
                end_game_screen()
                run = False
            else:
                continue
        
        if len(enemies) == 0:
            level += 1
            wave_length += 5
            enemy_vel += 0.2
            for i in range(wave_length):
                enemy = Enemy(random.randrange(100, WIDTH - 100), random.randrange(-1500, -100), random.choice(["red", "green", "yellow"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and player.x - player_vel > 0:
            player.x -= player_vel
        if (keys[pygame.K_d]or keys[pygame.K_RIGHT]) and player.x + player_vel + player.get_width() < WIDTH:
            player.x += player_vel
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and player.y - player_vel > 0:
            player.y -= player_vel
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and player.y + player_vel + player.get_height() < HEIGHT:
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, 100) == 1 and enemy.y > 0:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)
            
        player.move_lasers(-laser_vel, enemies)

def main_menu():
    title_font = pygame.font.SysFont("comicsans", 40)
    run = True
    while run:
        WIN.blit(BG, (0,0))
        title_label = title_font.render("Press any key to begin", 1, (255,255,255))
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 300))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                main()
    pygame.quit()

main_menu()
main() 