import os
import pygame
import time
import random
import pickle
import sys

# inicjalizacja modułu pygame
pygame.font.init()

# ustawienia okna gry
WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space shooter 420803")

# grafiki statków kosmicznych
RED_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_red.png")), (int(WIDTH * 0.15), int(HEIGHT * 0.15)))
YELLOW_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_yellow.png")), (int(WIDTH * 0.15), int(HEIGHT * 0.15)))
GREEN_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_green.png")), (int(WIDTH * 0.15), int(HEIGHT * 0.15)))

BLUE_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "ship_blue.png")), (int(WIDTH * 0.2), int(HEIGHT * 0.2)))

# grafiki laserów
RED_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_red.png")), (int(WIDTH * 0.1), int(HEIGHT * 0.1)))
YELLOW_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_yellow.png")), (int(WIDTH * 0.1), int(HEIGHT * 0.1)))
GREEN_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_green.png")), (int(WIDTH * 0.1), int(HEIGHT * 0.1)))

BLUE_LASER = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "laser_blue.png")), (int(WIDTH * 0.12), int(HEIGHT * 0.12)))

# tło gry
try:
    BG = pygame.transform.scale(pygame.image.load(os.path.join("grafika", "space_background.png")), (WIDTH, HEIGHT))
except pygame.error as e:
    print(f"Error loading background image: {e}")
    pygame.quit()
    sys.exit()

# funkcja dekorująca, obliczajaca czas wykonywania się danej funkcji (uzywamy jej na main -> czas gry w sekundach)
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            results = func(*args, **kwargs)
        except Exception as e:
            print(f"An error occurred: {e}")
            results = None
        end_time = time.time()
        execution_time = end_time - start_time
        return results, execution_time

    return wrapper

# klasa reprezentująca laser
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
            #sprawdz kolizję lasera z obiektem(statkiem)
            offset_x = obj.x - self.x
            offset_y = obj.y - self.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        return False
        
# klasa reprezentująca statek kosmiczny
class Ship:
    COOLDOWN = 15  # ile ms miedzy kolejnymi strzałami

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = [] #lista laserow statku
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
                #usuń lasery, które opuściły obszar ekranu
                self.lasers.remove(laser)
            elif laser.collision(obj):
                #sprawdź kolizję lasera z obiektem(statkiem)
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        #zarządzanie czasem odstępu między kolejnymi strzałami
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        #strzelaj tylko jeśli cooldown minął
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 30, self.y - 10, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

# klasa reprezentująca gracza
class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = BLUE_SPACE_SHIP
        self.laser_img = BLUE_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.score = 0
        self.nickname = ""

        self.nickname_font = pygame.font.SysFont("helvetica", 30)
        self.nickname_input = ""
        self.nickname_set = False

    def move_lasers(self, vel, objs):
        global score
        self.cooldown()
        laser_to_remove = []

        for laser in self.lasers[:]: #iteruj przez kopie listy
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                #dodaj laser do listy do usuniecia jesli opusci ekran
                laser_to_remove.append(laser)
            else:
                for obj in objs:
                    if isinstance(obj, Enemy) and laser.collision(obj):
                        objs.remove(obj)
                        laser_to_remove.append(laser)
                        score += 2
                    elif laser.collision(obj) and isinstance(obj, Enemy):
                        self.lasers.remove(laser)

        for laser in laser_to_remove:
            self.lasers.remove(laser)

    def set_nickname(self):
        if not self.nickname:
            self.nickname = input("Enter your nickname: ")
            self.nickname_set = True

    #zwracanie długości obiektu
    def __len__(self):
        return len(self.nickname) if self.nickname_set else 0
    
    #zwracanie reprezentacji tekstowej obiektu
    def __str__(self):
        return self.nickname if self.nickname_set else "No nickname"

    def draw(self, window):
        #rysuj gracza oraz pasek zdrowia
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        #rysuj pasek zdrowia gracza
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height() - 10, self.ship_img.get_width(), 7))
        pygame.draw.rect(window, (0, 255, 0),
                         (self.x, self.y + self.ship_img.get_height() - 10,
                          self.ship_img.get_width() * (self.health / self.max_health), 7))

# klasa reprezentująca wroga
class Enemy(Ship):
    #mapa kolorów statków wroga i ich laserów
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER),
        "yellow": (YELLOW_SPACE_SHIP, YELLOW_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def __del__(self):
        #dzialania wykonywane przy usuwaniu obiektu
        if game_state == "running":
            print(f"Enemy ship at ({self.x}, {self.y}) was destroyed.")

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            #strzelaj tylko jeśli cooldown minął
            laser = Laser(self.x + 20, self.y + 35, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def collision(self, obj):
        if isinstance(obj, Player):
            #sprawdź kolizję przeciwnika z graczem
            offset_x = obj.x - self.x
            offset_y = obj.y - self.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        return False

# funkcja sprawdzająca kolizje między obiektami
def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None

# funkcja zapisująca wynik gracza do pliku
def save_score(nickname, score):
    try:
        #spróbuj otworzyć plik z wynikami
        with open("highscores.txt", 'rb') as file:
            highscores = pickle.load(file)
    except (FileNotFoundError, EOFError):
        #jeżeli pli nie istnieje lub jest pusty, stwórz pustą listę
        highscores = []

    #dodaj nowy wynik do listy i posortuj malejąco
    highscores.append((nickname, score))
    highscores.sort(key=lambda x: x[1], reverse = True)

    #zapisz tylko 5 najlepszych wyników
    with open("highscores.txt", "wb") as file:
        pickle.dump(highscores[:5], file)

# funkcja wyświetlająca najlepsze wyniki
def display_highscores(nickname):
    try:
        with open("highscores.txt", "rb") as file:
            highscores = pickle.load(file)
    except (FileNotFoundError, EOFError):
        highscores = []

    print("Top 5 Highscores: ")
    for i, (name, score) in enumerate(highscores[:5], start = 1):
        if name == nickname:
            print(f"{i}. {name}: {score} (Your Score)")
        else:
            print(f"{i}. {name}: {score}")

game_state = "running"
# głóna funkcja gry z dekoratorem
@timing_decorator
def main():
    global score, game_state
    run = True
    pygame.font.init()
    FPS = 60
    level = 0
    lives = 3
    score = 0
    main_font = pygame.font.SysFont("helvetica", 30)
    lost_font = pygame.font.SysFont("helvetica", 40)

    #lista przeciwników
    enemies = []
    wave_length = 5
    enemy_vel = 1

    #szybkość poruszania się statków i strzałów laserowych
    player_vel = 5
    laser_vel = 7

    player = Player(300, 600)
    
    clock = pygame.time.Clock()

    #flaga informująca o przegranej
    lost = False
    lost_count = 0

    # funkcja ekranu końcowego
    def end_game_screen(player):
        global game_state
        WIN.blit(BG, (0, 0))
        end_label = lost_font.render(f"You lost. Your score: {score}", 1, (255, 255, 255))
        WIN.blit(end_label, (WIDTH / 2 - end_label.get_width() / 2, 350))

        pygame.display.update()
        pygame.time.delay(3000)
        
        player.set_nickname()
        save_score(player.nickname, score)
        #uzycie metody str i len do wyswietlenia pseudonimu gracza i jego dlugosci
        pseudonym = str(player)
        length_of_nickname = len(player)
        print(f"\nNickname: {pseudonym}")
        print(f"Length of nickname: {length_of_nickname}")

        global run
        run = False
        game_state = "ended"
    
    # funkcja do odświeżania okna gry
    def redraw_window():
        WIN.blit(BG, (0, 0))

        #wyświetlanie info o życiach, poziomie i wyniku
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))
        score_label = main_font.render(f"Score: {score}", 1, (255, 255, 255))

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        WIN.blit(score_label, (WIDTH / 2 - score_label.get_width() / 2, 10))

        #rysowanie przeciwników na ekranie
        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        pygame.display.update()

    #głóna pętla gry
    while run:
        clock.tick(FPS)
        redraw_window()

        #sprawdzanie warunków przegranej
        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        #obsługa ekranu po przegranej
        if lost:
            if lost_count > FPS * 3:
                player.set_nickname()
                save_score(player.nickname, score)
                display_highscores(player.nickname)
                end_game_screen(player)
            else:
                continue
        
        if game_state == "ended":
            break

        #dodanie nowej fali przeciwników (kolejny poziom) po zniszczeniu poprzedniej
        if len(enemies) == 0:
            level += 1
            wave_length += 5
            enemy_vel += 0.1
            for i in range(wave_length):
                enemy = Enemy(random.randrange(100, WIDTH - 100), random.randrange(-1500, -100), random.choice(["red", "green", "yellow"]))
                enemies.append(enemy)

        player.level_up_timer = FPS
        player.level_up_message = f"Level {level}"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        #poruszanie się gracza
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

        #ruch i strzelanie przeciwników
        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            #losowe strzelanie przeciwników
            if random.randrange(0, 150) == 1 and enemy.y > 0:
                enemy.shoot()

            #kolizje i reakcje na kolizje
            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        #ruch i znikanie laserów gracza po opuszczeniu ekranu   
        player.move_lasers(-laser_vel, enemies)

# uruchomienie gry i otrzymanie wyniku oraz czasu trwania
result, play_time = main()
#wyswietlanie czasu trwania rozgrywki
print(f"Player played for: {play_time:.2f} seconds.")

def main_menu():
    title_font = pygame.font.SysFont("helvetica", 50)
    run = True
    
    #główna pętla menu
    while run:
        global game_state
        game_state = "running"
        WIN.blit(BG, (0,0))
        title_label = title_font.render("Press any key to begin", 1, (255,255,255))
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 300))
        pygame.display.update()
        
        #obsługa zdarzeń pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                main()

    print(f"Player played for: {play_time:.2f} seconds")

    pygame.quit()
    main()

main_menu()
