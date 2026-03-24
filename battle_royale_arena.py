import pygame
import random
import math
import numpy as np
import time

# --- 1. Pygame aur Window Initialization ---
pygame.init()

# --- GAME STATE ---
GAME_STATE = "MENU"   # MENU / PLAYING / PAUSED / GAME_OVER

pygame.mixer.init()

lobby_music = pygame.mixer.Sound("audio/lobby.mp3")
battle_music = pygame.mixer.Sound("audio/battle.mp3")
hit_sound = pygame.mixer.Sound("audio/hit.mp3")
winner_sound = pygame.mixer.Sound("audio/winner.mp3")

lobby_music.set_volume(0.5)
battle_music.set_volume(0.5)
hit_sound.set_volume(0.7)
winner_sound.set_volume(0.7)

lobby_music.play(-1)

# --- 2. GLOBAL CONSTANTS ---
WIDTH, HEIGHT = 800, 800
PLAYER_HEALTH = 150
PLAYER_DEFAULT_ATTACK = 10
PLAYER_AMMO = 10
SHOOTING_RANGE = 300
CLOSE_DISTANCE = 40
TURN_SPEED = 0.1
POWER_PACK_RESPAWN_DELAY = 5
POWER_PACK_ATTACK_MAX = 5
ATTACK_INCREASE_AMOUNT = 10
PLAYER_MOVE_SPEED = 3 
VISION_CONE_LENGTH = 100
VISION_CONE_ANGLE = math.radians(60)
FIRE_ANGLE_THRESHOLD = math.radians(10)
PLAYER_TURN_SPEED = 0.15 
PLAYER_FIRE_RATE = 0.3 

# --- Screen Setup ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("5 Competing Agents Battle Royale")

# --- Fonts ---
font = pygame.font.Font(None, 24)
medium_title_font = pygame.font.Font(None, 60)
player_font = pygame.font.Font(None, 20)

# --- BUTTON FUNCTION ---
def draw_button(text, x, y, w, h, color, hover_color):
    mouse = pygame.mouse.get_pos()
    rect = pygame.Rect(x, y, w, h)

    # hover effect
    if rect.collidepoint(mouse):
        pygame.draw.rect(screen, hover_color, rect, border_radius=10)
    else:
        pygame.draw.rect(screen, color, rect, border_radius=10)

    # text center
    txt = font.render(text, True, (0,0,0))
    screen.blit(
        txt,
        (x + w//2 - txt.get_width()//2,
         y + h//2 - txt.get_height()//2)
    )

    return rect

start_btn_rect = None
exit_btn_rect = None
resume_btn_rect = None
restart_btn_rect = None
pause_exit_btn_rect = None
countdown_start_time = None
COUNTDOWN_DURATION = 5

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
MAGENTA_LIGHT = (255, 0, 255)
CYAN_LIGHT = (0, 255, 255)


# --- Global Item Variables ---
ITEM_TRACKER = {
    'power_pack_rects': [],
    'last_pack_picked_up_time': 0.0
}


# --- Item Images Load Karna (PATHS AS PROVIDED - NO CHANGE) ---
try:
    HEALTH_KIT_IMG = pygame.image.load('images/heal_firstaid-57fc8495.png').convert_alpha()
    HEALTH_KIT_IMG = pygame.transform.scale(HEALTH_KIT_IMG, (35, 35))
    
    AMMO_PACK_IMG = pygame.image.load('images/ammo_300magnum-dacdd5f3.png').convert_alpha()
    AMMO_PACK_IMG = pygame.transform.scale(AMMO_PACK_IMG, (35, 35))
    
    POWER_FLASK_IMG = pygame.image.load('images/power flask bottle.png').convert_alpha()
    POWER_FLASK_IMG = pygame.transform.scale(POWER_FLASK_IMG, (35, 35))
    
    RESTART_ICON = pygame.image.load('images/restart.png').convert_alpha()
    RESTART_ICON = pygame.transform.scale(RESTART_ICON, (60, 60))
    restart_icon_rect = pygame.Rect(WIDTH//2 - 30, HEIGHT//2 + 120, 60, 60)
    
    PAUSE_ICON = pygame.image.load('images/pause.png').convert_alpha()
    PAUSE_ICON = pygame.transform.scale(PAUSE_ICON, (40, 40))
    pause_icon_rect = pygame.Rect(WIDTH - 50, 10, 40, 40)
    
    MAP_BG_IMG = pygame.image.load('images/map.png').convert()
    MAP_BG_IMG = pygame.transform.scale(MAP_BG_IMG, (WIDTH, HEIGHT))
    USE_IMAGES = True
    print("Images loaded successfully.")
except pygame.error as e:
    USE_IMAGES = False
    MAP_BG_IMG = pygame.Surface((WIDTH, HEIGHT)); MAP_BG_IMG.fill(WHITE)


# --- Custom Draw Functions (Fallback) ---
def draw_gradient_rect(surface, rect, color1, color2):
    for i in range(rect.height):
        ratio = i / rect.height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (rect.x, rect.y + i), (rect.x + rect.width, rect.y + i))

def draw_health_kit(surface, rect):
    pygame.draw.rect(surface, RED, rect, border_radius=5)
    pygame.draw.line(surface, WHITE, (rect.x + 5, rect.y + rect.height // 2), (rect.x + rect.width - 5, rect.y + rect.height // 2), 3)

def draw_ammo_pack(surface, rect):
    pygame.draw.rect(surface, (150, 100, 50), rect, border_radius=3)
    pygame.draw.line(surface, (200, 150, 100), (rect.x, rect.y + 5), (rect.x + rect.width, rect.y + 5), 2)

# --- NEW: Vision Cone Drawing Function ---
def draw_vision_cone(surface, center_pos, facing_angle, color, cone_angle, cone_length):
    vision_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    light_color = (color[0], color[1], color[2], 50)

    start_angle = facing_angle - cone_angle / 2
    end_angle = facing_angle + cone_angle / 2

    points = [center_pos]
    for i in range(20):
        angle = start_angle + (end_angle - start_angle) * i / 19
        x = center_pos[0] + cone_length * math.cos(angle)
        y = center_pos[1] + cone_length * math.sin(angle)
        points.append((x, y))
    points.append(center_pos)

    if len(points) > 2:
        vision_color_with_alpha = (light_color[0], light_color[1], light_color[2], 50)
        pygame.draw.polygon(vision_surface, vision_color_with_alpha, points)

    surface.blit(vision_surface, (0, 0))

# --- 3. Bullet Class ---
class Bullet:
    def __init__(self, x, y, angle, speed, owner):
        self.rect = pygame.Rect(x, y, 5, 5)
        self.angle = angle
        self.speed = speed
        self.owner = owner
        self.vx = self.speed * math.cos(self.angle)
        self.vy = self.speed * math.sin(self.angle)

    def move(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

    def draw(self, surface):
        pygame.draw.circle(surface, self.owner.color, self.rect.center, 3)

# --- 4. Agent Class ---
class Agent:
    def __init__(self, x, y, color, name, max_health=100, attack_power=PLAYER_DEFAULT_ATTACK, initial_ammo=10, is_player=False):
        self.rect = pygame.Rect(x, y, 25, 25)
        self.color = color
        self.name = name
        self.health = max_health
        self.max_health = max_health
        self.attack = attack_power
        self.ammo = initial_ammo
        self.kills = 0
        self.last_fired_time = 0
        self.facing_angle = random.uniform(0, 2 * math.pi)
        self.is_player = is_player

    def draw(self, surface, font):
        # 1. Vision Cone Drawing
        draw_vision_cone(surface, self.rect.center, self.facing_angle, self.color, VISION_CONE_ANGLE, VISION_CONE_LENGTH)

        # 2. Player Body (Different shape for player)
        if self.is_player:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
            pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)
        else:
            pygame.draw.circle(surface, self.color, self.rect.center, 12)
            pygame.draw.circle(surface, BLACK, self.rect.center, 13, 1)

        # 3. Direction Pointer
        end_point = (
            self.rect.centerx + 15 * math.cos(self.facing_angle),
            self.rect.centery + 15 * math.sin(self.facing_angle)
        )
        pygame.draw.line(surface, BLACK, self.rect.center, end_point, 3)


        self.draw_health_bar(surface)
        self.draw_stats(surface, font)

    def draw_health_bar(self, surface):
        if self.health > 0:
            bar_x = self.rect.x
            bar_y = self.rect.y - 15
            bar_width = self.rect.width
            bar_height = 5
            health_ratio = self.health / self.max_health
            current_width = bar_width * health_ratio
            pygame.draw.rect(surface, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            health_color = RED if self.health < 30 else GREEN
            pygame.draw.rect(surface, health_color, (bar_x, bar_y, current_width, bar_height))

    def draw_stats(self, surface, font):
        # Player ka name aur stats
        name_text = font.render(f"{self.name} (K:{self.kills})", True, self.color)
        surface.blit(name_text, (self.rect.x, self.rect.y - 30))
        ammo_text = font.render(f'Ammo: {self.ammo}', True, BLACK)
        surface.blit(ammo_text, (self.rect.x, self.rect.y + self.rect.height + 5))

        if self.is_player:
            attack_text = font.render(f'ATK: {self.attack}', True, (150, 50, 0))
            surface.blit(attack_text, (self.rect.x, self.rect.y + self.rect.height + 20))


    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0

    def is_alive(self):
        return self.health > 0

    def fire_bullet(self, target_pos, all_bullets, fire_rate=0.5):
        current_time = time.time()
        if self.ammo > 0 and current_time - self.last_fired_time > fire_rate:
            self.ammo -= 1
            self.last_fired_time = current_time
            dx = target_pos[0] - self.rect.centerx
            dy = target_pos[1] - self.rect.centery
            fire_angle = math.atan2(dy, dx)
            
            if self.is_player:
                 self.facing_angle = fire_angle 
            
            new_bullet = Bullet(self.rect.centerx, self.rect.centery, fire_angle, 10, self)
            all_bullets.append(new_bullet)

# --- 5. Game Objects & Map (Interior walls removed for stability) ---
map_rect = MAP_BG_IMG.get_rect()

walls = [
    pygame.Rect(0, 0, 800, 50), pygame.Rect(0, 750, 800, 50),
    pygame.Rect(0, 0, 50, 800), pygame.Rect(750, 0, 50, 800),
]

def get_safe_pos(existing_items_rects):
    while True:
        pos = (random.randint(70, WIDTH - 70), random.randint(70, HEIGHT - 70))
        temp_rect = pygame.Rect(pos[0], pos[1], 25, 25)

        if any(temp_rect.colliderect(wall) for wall in walls):
            continue

        if any(temp_rect.colliderect(item) for item in existing_items_rects):
            continue

        return pos

def line_of_sight_clear(p1_rect, p2_rect, walls):
    x1, y1 = p1_rect.center
    x2, y2 = p2_rect.center
    num_steps = 20
    for i in range(1, num_steps):
        t = i / num_steps
        current_x = x1 + t * (x2 - x1)
        current_y = y1 + t * (y2 - y1)
        check_rect = pygame.Rect(current_x - 2, current_y - 2, 4, 4)
        if any(check_rect.colliderect(wall) for wall in walls):
            return False
    return True


def distance(a, b):
    ax, ay = a.center if hasattr(a, 'center') else a
    bx, by = b.center if hasattr(b, 'center') else b
    return math.hypot(ax - bx, ay - by)

def shortest_angle_diff(angle1, angle2):
    diff = angle2 - angle1
    while diff > math.pi:
        diff -= 2 * math.pi
    while diff < -math.pi:
        diff += 2 * math.pi
    return diff

# **PLAYER AGENT CHANGE**
all_agents = [
    Agent(*get_safe_pos([]), (50, 50, 200), "__You__", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO, is_player=True), # **PLAYER AGENT**
    Agent(*get_safe_pos([]), (0, 255, 255), "Player B", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO),
    Agent(*get_safe_pos([]), (255, 0, 255), "Player C", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO),
    Agent(*get_safe_pos([]), (255, 165, 0), "Player D", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO),
    Agent(*get_safe_pos([]), (128, 5, 128), "Player E", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO)
]
bullets = []

player_agent = all_agents[0] 

initial_items_rects = []
health_pack1 = pygame.Rect(*get_safe_pos(initial_items_rects), 25, 25)
initial_items_rects.append(health_pack1)
health_pack2 = pygame.Rect(*get_safe_pos(initial_items_rects), 25, 25)
initial_items_rects.append(health_pack2)
ammo_box1 = pygame.Rect(*get_safe_pos(initial_items_rects), 25, 25)
initial_items_rects.append(ammo_box1)
ammo_box2 = pygame.Rect(*get_safe_pos(initial_items_rects), 25, 25)
initial_items_rects.append(ammo_box2)


# --- 6. AI Logic (SAME) ---
def get_action(current_agent, target_agent, walls):

    if current_agent.health < 30:
        return "SEARCH_HEALTH"
    if current_agent.ammo == 0:
        return "SEARCH_AMMO"

    is_target_in_range = distance(current_agent.rect, target_agent.rect) < SHOOTING_RANGE
    is_vision_clear = line_of_sight_clear(current_agent.rect, target_agent.rect, walls)
    is_not_too_close = distance(current_agent.rect, target_agent.rect) > CLOSE_DISTANCE

    if is_target_in_range and is_vision_clear and is_not_too_close:
        return "ATTACK"

    if ITEM_TRACKER['power_pack_rects'] and current_agent.attack < PLAYER_DEFAULT_ATTACK + POWER_PACK_ATTACK_MAX:
        power_rect = ITEM_TRACKER['power_pack_rects'][0]
        if distance(current_agent.rect, power_rect) < 200:
            return "SEARCH_POWER"

    return "CHASE_TARGET"


# --- 7. Winner Display Function (SAME) ---
def display_winner(winner_agent, surface, frame_count):
    medium_font = pygame.font.Font(None, 60)
    msg_line1 = "CONGRATULATIONS!"
    msg_line2 = f"{winner_agent.name} WINS!"
    text1_surface = medium_font.render(msg_line1, True, winner_agent.color)
    text2_surface = medium_font.render(msg_line2, True, winner_agent.color)
    total_height = text1_surface.get_height() + text2_surface.get_height() + 10
    center_x = WIDTH // 2
    center_y = HEIGHT // 2 - total_height // 2 - 50
    shadow_color = BLACK
    offset = 3
    x1 = center_x - text1_surface.get_width() // 2 + math.sin(frame_count * 0.1) * 10
    y1 = center_y
    surface.blit(medium_font.render(msg_line1, True, shadow_color), (x1 + offset, y1 + offset))
    surface.blit(text1_surface, (x1, y1))
    x2 = center_x - text2_surface.get_width() // 2 - math.sin(frame_count * 0.1) * 10
    y2 = center_y + text1_surface.get_height() + 10
    surface.blit(medium_font.render(msg_line2, True, shadow_color), (x2 + offset, y2 + offset))
    surface.blit(text2_surface, (x2, y2))
    logo_size = 100
    logo_rect = pygame.Rect(center_x - logo_size // 2, y2 + text2_surface.get_height() + 20, logo_size, logo_size)
    pygame.draw.rect(surface, winner_agent.color, logo_rect, border_radius=15)
    pygame.draw.rect(surface, BLACK, logo_rect, 5, border_radius=15)


# --- MAIN MENU ---
def draw_menu():
    global start_btn_rect, exit_btn_rect
    screen.fill((20, 20, 30))

    title = medium_title_font.render("BATTLE ROYALE ARENA ", True, WHITE)

    screen.blit(title, (WIDTH//2 - title.get_width()//2, 250))
    start_btn_rect = draw_button("START", WIDTH//2 - 100, 320, 200, 50, GREEN, (0,255,150))
    exit_btn_rect  = draw_button("EXIT",  WIDTH//2 - 100, 400, 200, 50, RED, (255,100,100))

# --- PAUSE MENU ---
def draw_pause_menu():
    global resume_btn_rect, restart_btn_rect, pause_exit_btn_rect
    screen.fill((30, 30, 40))

    title = medium_title_font.render("PAUSED", True, WHITE)

    screen.blit(title, (WIDTH//2 - title.get_width()//2, 250))

    resume_btn_rect  = draw_button("RESUME", WIDTH//2 - 100, 300, 200, 50, GREEN, (0,255,150))
    restart_btn_rect = draw_button("RESTART", WIDTH//2 - 100, 370, 200, 50, (200,200,0), (255,255,100))
    pause_exit_btn_rect = draw_button("EXIT", WIDTH//2 - 100, 440, 200, 50, RED, (255,100,100))

def restart_game():
    global all_agents, bullets, game_over, winner, GAME_STATE, player_agent, countdown_start_time

    bullets.clear()

    all_agents = [
        Agent(*get_safe_pos([]), (50, 50, 200), "__You__", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO, is_player=True),
        Agent(*get_safe_pos([]), (0, 255, 255), "Player B", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO),
        Agent(*get_safe_pos([]), (255, 0, 255), "Player C", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO),
        Agent(*get_safe_pos([]), (255, 165, 0), "Player D", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO),
        Agent(*get_safe_pos([]), (128, 5, 128), "Player E", PLAYER_HEALTH, PLAYER_DEFAULT_ATTACK, PLAYER_AMMO)
    ]

    player_agent = all_agents[0]

    game_over = False
    winner = None

    countdown_start_time = None
    
    winner_sound.stop()
    battle_music.stop()
    lobby_music.stop()

    GAME_STATE = "MENU"
    battle_music.play(-1)

# --- 8. Main Loop ---
clock = pygame.time.Clock()
running = True
game_over = False
winner = None
frame_count = 0

while running:
    clock.tick(60)
    frame_count += 1
    current_time = time.time()

    # --- EVENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # MENU CONTROLS
        if GAME_STATE == "MENU":
        # KEYBOARD
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    GAME_STATE = "COUNTDOWN"
                    countdown_start_time = time.time()
                    lobby_music.stop()

                elif event.key == pygame.K_3:
                    running = False

        # 🔥 MOUSE (SEPARATE BLOCK)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn_rect and start_btn_rect.collidepoint(event.pos):
                    print("START CLICKED")
                    GAME_STATE = "COUNTDOWN"
                    countdown_start_time = time.time()
                    lobby_music.stop()

                elif exit_btn_rect and exit_btn_rect.collidepoint(event.pos):
                    print("EXIT CLICKED")
                    running = False
        
        # PAUSE TOGGLE (ESC)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if GAME_STATE == "PLAYING":
                    GAME_STATE = "PAUSED"
                    battle_music.stop()
                elif GAME_STATE == "PAUSED":
                    GAME_STATE = "PLAYING"
                    battle_music.play(-1)

        # PAUSE MENU CONTROLS
        if GAME_STATE == "PAUSED":

            # KEYBOARD
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    GAME_STATE = "PLAYING"
                    battle_music.play(-1)

                elif event.key == pygame.K_t:
                    restart_game()

                elif event.key == pygame.K_e:
                    running = False

            # 🔥 MOUSE CLICK (YAHI ADD KARNA HAI)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_btn_rect and resume_btn_rect.collidepoint(event.pos):
                    GAME_STATE = "PLAYING"
                    battle_music.play(-1)

                elif restart_btn_rect and restart_btn_rect.collidepoint(event.pos):
                    restart_game()

                elif pause_exit_btn_rect and pause_exit_btn_rect.collidepoint(event.pos):
                    running = False
        

        # GAME OVER RESTART
        if game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    restart_game()

        # PLAYER FIRE
        if GAME_STATE == "PLAYING" and not game_over and player_agent.is_alive():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                player_agent.fire_bullet(mouse_pos, bullets, fire_rate=PLAYER_FIRE_RATE)

        if GAME_STATE == "PLAYING":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pause_icon_rect and pause_icon_rect.collidepoint(event.pos):
                    GAME_STATE = "PAUSED"
                    battle_music.stop()

        if game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_icon_rect.collidepoint(event.pos):
                    restart_game()

    # --- STATE SCREENS ---
    if GAME_STATE == "MENU":
        draw_menu()
        pygame.display.flip()
        continue

    if GAME_STATE == "PAUSED":
        draw_pause_menu()
        pygame.display.flip()
        continue

    if GAME_STATE == "COUNTDOWN":
        screen.fill((10, 10, 20))

        if countdown_start_time is not None:
            elapsed = time.time() - countdown_start_time
        else:
            elapsed = 0
            
        remaining = max(0, COUNTDOWN_DURATION - int(elapsed))

        countdown_text = medium_title_font.render(
            str(remaining if remaining > 0 else "GO!"),
            True,
            WHITE
        )

        screen.blit(
            countdown_text,
            (WIDTH//2 - countdown_text.get_width()//2,
             HEIGHT//2 - countdown_text.get_height()//2)
        )

        pygame.display.flip()

        # countdown खत्म → game start
        if elapsed >= COUNTDOWN_DURATION:
            GAME_STATE = "PLAYING"
            battle_music.play(-1)

        continue

    # --- GAME LOGIC ---
    if GAME_STATE == "PLAYING" and not game_over:
        alive_agents = [agent for agent in all_agents if agent.is_alive()]

        if len(alive_agents) <= 1:
            game_over = True
            winner = alive_agents[0] if alive_agents else None
            battle_music.stop()
            winner_sound.play()



    


        # --- Player Input Processing (UPDATED FOR SCREEN-RELATIVE MOVEMENT) ---
        if player_agent.is_alive():
            keys = pygame.key.get_pressed()
            
            # Rotation (E for Anticlockwise, R for Clockwise)
            if keys[pygame.K_e]:
                player_agent.facing_angle -= PLAYER_TURN_SPEED
            if keys[pygame.K_r]:
                player_agent.facing_angle += PLAYER_TURN_SPEED
            
            # Movement Calculation (Screen-Relative)
            move_x, move_y = 0, 0
            
            # Up (Screen Y decrease) / Down (Screen Y increase)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                move_y -= PLAYER_MOVE_SPEED
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                move_y += PLAYER_MOVE_SPEED
            
            # Left (Screen X decrease) / Right (Screen X increase)
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move_x -= PLAYER_MOVE_SPEED
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move_x += PLAYER_MOVE_SPEED

            # Normalize diagonal movement speed (optional, but good practice)
            if move_x != 0 and move_y != 0:
                move_factor = 1 / math.sqrt(2)
                move_x *= move_factor
                move_y *= move_factor
            
            # Apply movement and check collision
            old_rect = player_agent.rect.copy()
            player_agent.rect.x += move_x
            player_agent.rect.y += move_y

            for wall in walls:
                if player_agent.rect.colliderect(wall):
                    player_agent.rect = old_rect
                    break

            # Item Pickup Logic (Player - SAME)
            all_item_rects_for_spawn = [health_pack1, health_pack2, ammo_box1, ammo_box2]
            if ITEM_TRACKER['power_pack_rects']: all_item_rects_for_spawn.append(ITEM_TRACKER['power_pack_rects'][0])
            
            # Health Pack
            for h_pack in [health_pack1, health_pack2]:
                if player_agent.rect.colliderect(h_pack):
                    player_agent.health = min(player_agent.max_health, player_agent.health + 30)
                    if h_pack == health_pack1: 
                        health_pack1.x, health_pack1.y = get_safe_pos(all_item_rects_for_spawn)
                    else: 
                        health_pack2.x, health_pack2.y = get_safe_pos(all_item_rects_for_spawn)
            # Ammo Pack
            for a_pack in [ammo_box1, ammo_box2]:
                if player_agent.rect.colliderect(a_pack):
                    player_agent.ammo += 10
                    if a_pack == ammo_box1: 
                        ammo_box1.x, ammo_box1.y = get_safe_pos(all_item_rects_for_spawn)
                    else: 
                        ammo_box2.x, ammo_box2.y = get_safe_pos(all_item_rects_for_spawn)

            # Power Pack
            if ITEM_TRACKER['power_pack_rects'] and player_agent.rect.colliderect(ITEM_TRACKER['power_pack_rects'][0]):
                if player_agent.attack < PLAYER_DEFAULT_ATTACK + POWER_PACK_ATTACK_MAX:
                    player_agent.attack += ATTACK_INCREASE_AMOUNT
                ITEM_TRACKER['power_pack_rects'].pop(0)
                ITEM_TRACKER['last_pack_picked_up_time'] = current_time
            
            player_agent.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))


        # --- AI Agents logic (SAME) ---
        for current_agent in alive_agents:
            if current_agent.is_player: 
                continue

            possible_targets = [agent for agent in alive_agents if agent != current_agent]
            if not possible_targets: continue

            target_agent = min(possible_targets, key=lambda p: distance(current_agent.rect, p.rect))
            action = get_action(current_agent, target_agent, walls)

            # --- Rotation Logic (AI) ---
            if action == "ATTACK" or action == "CHASE_TARGET":
                dx = target_agent.rect.centerx - current_agent.rect.centerx
                dy = target_agent.rect.centery - current_agent.rect.centery
                target_angle = math.atan2(dy, dx)
                angle_diff = shortest_angle_diff(current_agent.facing_angle, target_angle)

                if abs(angle_diff) > 0.05:
                    current_agent.facing_angle += math.copysign(TURN_SPEED, angle_diff)
                else:
                    current_agent.facing_angle = target_angle

            else:
                current_agent.facing_angle += random.uniform(-0.05, 0.05)


            # --- Perform Action (AI) ---
            if action == "ATTACK":
                dx = target_agent.rect.centerx - current_agent.rect.centerx
                dy = target_agent.rect.centery - current_agent.rect.centery
                angle_to_target = math.atan2(dy, dx)
                angle_error = abs(shortest_angle_diff(current_agent.facing_angle, angle_to_target))

                if angle_error < FIRE_ANGLE_THRESHOLD:
                    current_agent.fire_bullet(target_agent.rect.center, bullets)

            # Movement logic (AI) - AI still uses directional movement toward target
            old_rect = current_agent.rect.copy()
            move_speed = 0

            if action in ["CHASE_TARGET", "SEARCH_HEALTH", "SEARCH_AMMO", "SEARCH_POWER"]:
                move_speed = PLAYER_MOVE_SPEED * 1.25 if "SEARCH" in action else PLAYER_MOVE_SPEED

                if action == "CHASE_TARGET":
                    target_item_rect = target_agent.rect
                    if distance(current_agent.rect, target_agent.rect) < CLOSE_DISTANCE:
                        move_speed *= -0.5 

                elif action == "SEARCH_HEALTH":
                    all_health_packs = [health_pack1, health_pack2]
                    target_item_rect = min(all_health_packs, key=lambda p: distance(current_agent.rect, p))
                elif action == "SEARCH_AMMO":
                    all_ammo_packs = [ammo_box1, ammo_box2]
                    target_item_rect = min(all_ammo_packs, key=lambda p: distance(current_agent.rect, p))
                elif action == "SEARCH_POWER" and ITEM_TRACKER['power_pack_rects']:
                    target_item_rect = ITEM_TRACKER['power_pack_rects'][0]
                else:
                    target_item_rect = None


                if target_item_rect:
                    dx = target_item_rect.centerx - current_agent.rect.centerx
                    dy = target_item_rect.centery - current_agent.rect.centery
                    angle = math.atan2(dy, dx)

                    current_agent.rect.x += move_speed * math.cos(angle)
                    current_agent.rect.y += move_speed * math.sin(angle)

            else:
                move_speed = PLAYER_MOVE_SPEED * 0.5
                current_agent.rect.x += move_speed * math.cos(current_agent.facing_angle)
                current_agent.rect.y += move_speed * math.sin(current_agent.facing_angle)


            # AI Wall Collision
            for wall in walls:
                if current_agent.rect.colliderect(wall):
                    current_agent.rect = old_rect
                    current_agent.facing_angle = random.uniform(0, 2 * math.pi)

            # AI Item Pickup Logic
            all_item_rects_for_spawn = [health_pack1, health_pack2, ammo_box1, ammo_box2]
            if ITEM_TRACKER['power_pack_rects']: all_item_rects_for_spawn.append(ITEM_TRACKER['power_pack_rects'][0])

            if action == "SEARCH_HEALTH":
                target_health_pack = min([health_pack1, health_pack2], key=lambda p: distance(current_agent.rect, p))
                if current_agent.rect.colliderect(target_health_pack):
                    current_agent.health = min(current_agent.max_health, current_agent.health + 30)
                    if target_health_pack == health_pack1: health_pack1.x, health_pack1.y = get_safe_pos(all_item_rects_for_spawn)
                    else: health_pack2.x, health_pack2.y = get_safe_pos(all_item_rects_for_spawn)

            elif action == "SEARCH_AMMO":
                target_ammo_pack = min([ammo_box1, ammo_box2], key=lambda p: distance(current_agent.rect, p))
                if current_agent.rect.colliderect(target_ammo_pack):
                    current_agent.ammo += 10
                    if target_ammo_pack == ammo_box1: ammo_box1.x, ammo_box1.y = get_safe_pos(all_item_rects_for_spawn)
                    else: ammo_box2.x, ammo_box2.y = get_safe_pos(all_item_rects_for_spawn)

            elif action == "SEARCH_POWER":
                if ITEM_TRACKER['power_pack_rects'] and current_agent.rect.colliderect(ITEM_TRACKER['power_pack_rects'][0]):
                    if current_agent.attack < PLAYER_DEFAULT_ATTACK + POWER_PACK_ATTACK_MAX:
                        current_agent.attack += ATTACK_INCREASE_AMOUNT
                    ITEM_TRACKER['power_pack_rects'].pop(0)
                    ITEM_TRACKER['last_pack_picked_up_time'] = current_time

            current_agent.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        # Bullet movement and collision (SAME)
        for bullet in bullets[:]:
            bullet.move()
            if any(bullet.rect.colliderect(wall) for wall in walls):
                bullets.remove(bullet)
                continue
            for agent in alive_agents:
                if bullet.owner != agent and bullet.rect.colliderect(agent.rect):
                    agent.take_damage(bullet.owner.attack)
                    hit_sound.play()
                    if not agent.is_alive(): 
                         bullet.owner.kills += 1
                    bullets.remove(bullet)
                    break

    # --- Drawing (SAME) ---

    if GAME_STATE == "MENU":
        draw_menu()
        pygame.display.flip()
        continue
    
    screen.fill(WHITE)
    screen.blit(MAP_BG_IMG, map_rect)

    if GAME_STATE == "PLAYING":
        screen.blit(PAUSE_ICON, pause_icon_rect)

    if USE_IMAGES:
        screen.blit(HEALTH_KIT_IMG, health_pack1)
        screen.blit(HEALTH_KIT_IMG, health_pack2)
        screen.blit(AMMO_PACK_IMG, ammo_box1)
        screen.blit(AMMO_PACK_IMG, ammo_box2)
    else:
        draw_health_kit(screen, health_pack1)
        draw_health_kit(screen, health_pack2)
        draw_ammo_pack(screen, ammo_box1)
        draw_ammo_pack(screen, ammo_box2)

    if ITEM_TRACKER['power_pack_rects']:
        power_rect = ITEM_TRACKER['power_pack_rects'][0]
        if USE_IMAGES:
            screen.blit(POWER_FLASK_IMG, power_rect)
        else:
            draw_gradient_rect(screen, power_rect, MAGENTA_LIGHT, CYAN_LIGHT)
            pygame.draw.rect(screen, BLACK, power_rect, 1)

    for bullet in bullets:
        bullet.draw(screen)
    for agent in all_agents:
        if agent.is_alive():
            agent.draw(screen, player_font)
            
    # Player Instructions (UPDATED)
    if player_agent.is_alive() and not game_over:
        instruction_text = font.render('Controls: W/S/A/D or Arrows (Screen Move), E/R (Rotate), Left Click (Fire)', True, BLACK)
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT - 20))


    if game_over and winner:
        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill(BLACK)
        fade_surface.set_alpha(150)
        screen.blit(fade_surface, (0, 0))
        display_winner(winner, screen, frame_count)
        screen.blit(RESTART_ICON, restart_icon_rect)

    pygame.display.flip()

pygame.quit()