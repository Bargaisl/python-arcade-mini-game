import pygame
import random

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("K.I.A Simulator Fly 9/11")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (150, 150, 150)
BROWN = (139, 69, 19)
DARK_RED = (139, 0, 0)
SKY_BLUE = (135, 206, 235)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

initial_game_speed = 10
game_speed = initial_game_speed
speed_increase_interval = 5000

try:
    player_image_orig = pygame.image.load("plane.png").convert_alpha()
    player_image = pygame.transform.scale(player_image_orig, (80, 40))

    cactus_image_orig = pygame.image.load("tower.png").convert_alpha()
    cactus_image = pygame.transform.scale(cactus_image_orig, (60, 120))
except pygame.error as e:
    print(f"Не удалось загрузить изображение: {e}")
    player_image = pygame.Surface((80, 40), pygame.SRCALPHA)
    player_image.fill(RED)
    pygame.draw.rect(player_image, BLACK, player_image.get_rect(), 1)
    cactus_image = pygame.Surface((60, 120), pygame.SRCALPHA)
    cactus_image.fill(DARK_GRAY)
    pygame.draw.rect(cactus_image, BLACK, cactus_image.get_rect(), 1)


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.particles = []
        self.center = center
        self.particle_count = 25
        self.particle_lifetime = 25
        self.particle_speed_range = (1, 6)

        for _ in range(self.particle_count):
            x = self.center[0]
            y = self.center[1]
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(self.particle_speed_range[0], self.particle_speed_range[1])
            color = random.choice([YELLOW, ORANGE, RED, DARK_RED, DARK_GRAY])
            size = random.randint(2, 7)
            lifetime = random.randint(self.particle_lifetime // 2, self.particle_lifetime)

            dx = speed * pygame.math.Vector2(1, 0).rotate_rad(angle)[0]
            dy = speed * pygame.math.Vector2(1, 0).rotate_rad(angle)[1]

            self.particles.append({
                'x': x, 'y': y, 'dx': dx, 'dy': dy,
                'color': color, 'size': size, 'lifetime': lifetime
            })
        self.alive = True

    def update(self):
        if not self.particles:
            self.alive = False
            return

        active_particles = []
        for p in self.particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['lifetime'] -= 1
            p['size'] = max(1, p['size'] * 0.96)

            if p['lifetime'] > 0:
                active_particles.append(p)
        self.particles = active_particles

        if not self.particles:
            self.alive = False

    def draw(self, surface):
        for p in self.particles:
            pygame.draw.circle(surface, p['color'], (int(p['x']), int(p['y'])), int(p['size']))


explosions = []

player_x = 50
player_y = SCREEN_HEIGHT - 105
player_jump = False
jump_speed = 16
gravity = 1
player_y_velocity = 0

obstacle_x = SCREEN_WIDTH
obstacle_y = SCREEN_HEIGHT - 130

ground_y = SCREEN_HEIGHT - 10
ground_height = 10
building_min_height = 50
building_max_height = 120
building_min_width = 30
building_max_width = 70
building_spacing = 180
buildings = []

score = 0
last_speed_increase_time = pygame.time.get_ticks()
game_over = False
game_started = False


def create_building(previous_building_right_x):
    height = random.randint(building_min_height, building_max_height)
    width = random.randint(building_min_width, building_max_width)

    x_position = previous_building_right_x + random.randint(building_spacing, building_spacing + 100)
    y_position = ground_y - height
    color = random.choice([DARK_GRAY, LIGHT_GRAY, BROWN, DARK_RED, (70, 70, 70)])

    windows = []
    num_windows_rows = random.randint(1, int(height / 30))
    num_windows_cols = random.randint(1, int(width / 20))

    window_width = 8
    window_height = 12
    padding_x = (width - num_windows_cols * window_width) / (num_windows_cols + 1)
    padding_y = (height - num_windows_rows * window_height) / (num_windows_rows + 1)

    for r in range(num_windows_rows):
        for c in range(num_windows_cols):
            window_x_relative = padding_x + c * (window_width + padding_x)
            window_y_on_building = padding_y + r * (window_height + padding_y)
            window_y_absolute = y_position + window_y_on_building

            windows.append((window_x_relative, window_y_absolute, window_width, window_height))

    return [x_position, y_position, width, height, color, windows]


def display_text(text, font_size, color, y_offset=0, x_offset=0, center_x=True, font_name=None):
    try:
        font = pygame.font.Font(font_name, font_size)
    except:
        font = pygame.font.Font(None, font_size)

    text_surface = font.render(text, True, color)
    if center_x:
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2 + x_offset, SCREEN_HEIGHT // 2 + y_offset))
    else:
        text_rect = text_surface.get_rect(topleft=(x_offset, y_offset))
    screen.blit(text_surface, text_rect)


def reset_game():
    global game_speed, score, obstacle_x, player_y, player_jump, player_y_velocity
    global buildings, game_over, last_speed_increase_time, explosions, game_started

    game_speed = initial_game_speed
    score = 0
    obstacle_x = SCREEN_WIDTH + random.randint(100, 300)
    player_y = SCREEN_HEIGHT - 105
    player_jump = False
    player_y_velocity = 0

    buildings.clear()
    current_building_edge_x = 0
    for _ in range(10):
        building = create_building(current_building_edge_x)
        buildings.append(building)
        current_building_edge_x = building[0] + building[2]
        if current_building_edge_x > SCREEN_WIDTH + 200:
            break

    game_over = False
    last_speed_increase_time = pygame.time.get_ticks()
    explosions.clear()


try:
    pygame.mixer.music.load("song.mp3")
    pygame.mixer.music.play(-1, 0.0)
    pygame.mixer.music.set_volume(0.3)
except pygame.error as e:
    print(f"Не удалось загрузить или воспроизвести музыку: {e}")

explosion_sound = None
try:
    explosion_sound = pygame.mixer.Sound("explosion.wav")
    explosion_sound.set_volume(0.6)
except pygame.error as e:
    print(f"Не удалось загрузить звук взрыва: {e}")

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(SKY_BLUE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not game_started:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                game_started = True
                reset_game()
        else:
            if event.type == pygame.KEYDOWN:
                if not game_over:
                    if (event.key == pygame.K_SPACE or event.key == pygame.K_UP) and not player_jump:
                        player_jump = True
                        player_y_velocity = -jump_speed
                elif event.key == pygame.K_RETURN and game_over:
                    reset_game()

    if not game_started:
        display_text("K.I.A Fly 9/11", 70, DARK_RED, -60)
        display_text("Нажмите любую клавишу или кликните, чтобы начать", 30, BLACK, 10)
        display_text("Управление: ПРОБЕЛ или СТРЕЛКА ВВЕРХ - прыжок", 24, BLACK, 60)
        display_text("Цель: ВРЕЗАТЬСЯ В БАШНЮ!", 24, BLACK, 90)
    else:
        if not game_over:
            current_time = pygame.time.get_ticks()
            if current_time - last_speed_increase_time > speed_increase_interval:
                game_speed += 0.5
                last_speed_increase_time = current_time

            if player_jump:
                player_y += player_y_velocity
                player_y_velocity += gravity
                if player_y >= SCREEN_HEIGHT - 105:
                    player_y = SCREEN_HEIGHT - 105
                    player_jump = False
                    player_y_velocity = 0

            obstacle_x -= game_speed
            if obstacle_x < -cactus_image.get_width():
                obstacle_x = SCREEN_WIDTH + random.randint(50, 250)
                score += 1

            player_rect = pygame.Rect(player_x, player_y, player_image.get_width(), player_image.get_height())
            obstacle_rect = pygame.Rect(obstacle_x, obstacle_y, cactus_image.get_width(), cactus_image.get_height())

            if player_rect.colliderect(obstacle_rect):
                game_over = True
                explosion_center_x = obstacle_x + cactus_image.get_width() / 2
                explosion_center_y = player_y + player_image.get_height() / 2
                explosions.append(Explosion((explosion_center_x, explosion_center_y)))
                if explosion_sound:
                    explosion_sound.play()

        for exp in list(explosions):
            exp.update()
            if not exp.alive:
                explosions.remove(exp)
            else:
                exp.draw(screen)

        pygame.draw.rect(screen, BLACK, (0, ground_y, SCREEN_WIDTH, ground_height))

        building_speed_multiplier = 0.5
        for building_data in buildings:
            if not game_over:
                building_data[0] -= game_speed * building_speed_multiplier

            pygame.draw.rect(screen, building_data[4],
                             (building_data[0], building_data[1], building_data[2], building_data[3]))

            roof_height = 15
            roof_color = (
            min(building_data[4][0] + 20, 255), min(building_data[4][1] + 20, 255), min(building_data[4][2] + 20, 255))
            pygame.draw.polygon(screen, roof_color, [
                (building_data[0], building_data[1]),
                (building_data[0] + building_data[2] // 2, building_data[1] - roof_height),
                (building_data[0] + building_data[2], building_data[1])
            ])

            for window_info in building_data[5]:
                window_draw_x = building_data[0] + window_info[0]
                window_draw_y = window_info[1]
                pygame.draw.rect(screen, (200, 200, 255),
                                 (window_draw_x, window_draw_y, window_info[2], window_info[3]))

        if buildings and buildings[0][0] + buildings[0][2] < 0:
            buildings.pop(0)
            last_building_right_x = buildings[-1][0] + buildings[-1][2] if buildings else 0
            new_building = create_building(max(SCREEN_WIDTH, last_building_right_x))
            buildings.append(new_building)
        elif not buildings and not game_over:
            buildings.append(create_building(0))

        if not game_over or any(exp.alive for exp in explosions):
            screen.blit(player_image, (player_x, player_y))

        if not game_over:
            screen.blit(cactus_image, (obstacle_x, obstacle_y))
        elif game_over and any(exp.alive for exp in explosions):
            screen.blit(cactus_image, (obstacle_x, obstacle_y))

        display_text(f"Score: {score}", 36, BLACK, 10, 10, center_x=False)
        display_text(f"Speed: {game_speed:.1f}", 24, BLACK, 40, 10, center_x=False)

        if game_over and not any(exp.alive for exp in explosions):
            display_text("ВЫ ПОБЕДИЛИ", 70, DARK_RED, -40)
            display_text(f"ВАШ СЧЕТ: {score}, ЧЕГО НЕ ВРЕЗАЛСЯ РАНЬШЕ?", 40, BLACK, 20)
            display_text("Нажми ENTER для рестарта", 30, BLACK, 70)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
