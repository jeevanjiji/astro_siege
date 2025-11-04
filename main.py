import math
import random
import asyncio
import pygame
from pygame.locals import *
from pygame import mixer

print("Game Loaded!")

# Particle class for visual effects
class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # Gravity
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = int(self.size * (self.lifetime / self.max_lifetime))
        if size > 0:
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, alpha)
            pygame.draw.circle(s, color_with_alpha, (size, size), size)
            screen.blit(s, (int(self.x - size), int(self.y - size)))

# Power-up class
class PowerUp:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name
        self.vy = 2
        self.active = True
        self.size = 32
        # Colors for different power-ups
        self.colors = {
            "multi_shot": (255, 100, 255),
            "shield": (100, 200, 255),
            "slow_motion": (100, 255, 100),
            "rapid_fire": (255, 200, 100)
        }
        self.color = self.colors.get(type_name, (255, 255, 255))
    
    def update(self):
        self.y += self.vy
        return self.y < 600
    
    def draw(self, screen):
        # Draw power-up box with glow
        glow_size = self.size + 10
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 50), (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))
        
        # Main power-up
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), self.size, self.size), 3)
        pygame.draw.rect(screen, (*self.color, 100), (int(self.x) + 3, int(self.y) + 3, self.size - 6, self.size - 6))
        
        # Letter indicator
        font = pygame.font.Font(None, 24)
        letter = {"multi_shot": "M", "shield": "S", "slow_motion": "T", "rapid_fire": "R"}
        text = font.render(letter.get(self.type, "?"), True, self.color)
        text_rect = text.get_rect(center=(int(self.x + self.size/2), int(self.y + self.size/2)))
        screen.blit(text, text_rect)
    
    def collides_with(self, px, py, psize=64):
        return (self.x < px + psize and 
                self.x + self.size > px and 
                self.y < py + psize and 
                self.y + self.size > py)

# Score popup class
class ScorePopup:
    def __init__(self, x, y, score):
        self.x = x
        self.y = y
        self.score = score
        self.lifetime = 60
        self.vy = -2
    
    def update(self):
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen):
        alpha = int(255 * (self.lifetime / 60))
        font = pygame.font.Font(None, 32)
        text = font.render(f"+{self.score}", True, (255, 255, 100))
        text.set_alpha(alpha)
        screen.blit(text, (int(self.x), int(self.y)))

# Bullet trail class
class BulletTrail:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lifetime = 15
    
    def update(self):
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen):
        alpha = int(255 * (self.lifetime / 15))
        size = int(6 * (self.lifetime / 15))
        if size > 0:
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 100, alpha), (size, size), size)
            screen.blit(s, (int(self.x - size), int(self.y - size)))

# Global variables
screen = None
background = None
menu_bg = None
font = None
score_value = 0
lives = 3
max_lives = 3
heartImg = None
playerImg = None
playerX = 370
playerY = 480
playerX_change = 0
bulletImg = None
bulletX = 0
bulletY = 480
bulletY_change = 10
bullet_state = "ready"
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = 4
clock = None
running = True
game_state = "menu"  # "menu", "playing", "game_over", "paused", "settings", "tutorial"
previous_state = None
show_fps = False
show_tutorial = True  # Show tutorial on first play
transition_alpha = 0
transitioning = False
transition_speed = 5

# Settings
volume_music = 0.1
volume_sfx = 0.5
difficulty = "normal"  # "easy", "normal", "hard"
invincible = False
invincible_timer = 0
damage_flash_timer = 0

# Difficulty modifiers
difficulty_settings = {
    "easy": {"enemy_speed": 1.5, "enemy_drop_speed": 30, "starting_enemies": 3},
    "normal": {"enemy_speed": 2, "enemy_drop_speed": 40, "starting_enemies": 4},
    "hard": {"enemy_speed": 3, "enemy_drop_speed": 50, "starting_enemies": 6}
}

# Visual effects and game feel
particles = []
powerups = []
score_popups = []
bullet_trails = []
screen_shake_intensity = 0
screen_shake_duration = 0
bg_scroll_y = 0
bg_scroll_speed = 0.5

# Power-up states
active_powerups = {}
powerup_timers = {}
multi_shot_active = False
shield_active = False
slow_motion_active = False
rapid_fire_active = False
rapid_fire_cooldown = 0

# Input buffering
input_buffer = []
buffer_time = 10

# Enemy spawn animation
enemy_spawn_alpha = []

async def load_assets():
    """Load all game assets"""
    global screen, background, menu_bg, font, heartImg, playerImg, bulletImg, enemyImg, clock, volume_music
    
    pygame.init()
    mixer.init()  # Initialize mixer for sound
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Astro Siege")
    
    # Load and play background music
    try:
        mixer.music.load("assets/cb.mp3")
        mixer.music.set_volume(volume_music)
        mixer.music.play(-1)  # -1 means loop indefinitely
        print("Background music loaded successfully")
    except Exception as e:
        print(f"Could not load background music: {e}")
        # Try alternative file names
        try:
            mixer.music.load("cb.mp3")
            mixer.music.set_volume(volume_music)
            mixer.music.play(-1)
            print("Background music loaded from root directory")
        except Exception as e2:
            print(f"Background music not found: {e2}")
    
    # Try to load assets, use colored rectangles as fallbacks
    try:
        background = pygame.image.load('assets/background.png')
    except:
        background = pygame.Surface((800, 600))
        background.fill((0, 0, 50))  # Dark blue background
    
    try:
        menu_bg = pygame.image.load('assets/bg1.png')
    except:
        menu_bg = pygame.Surface((800, 600))
        menu_bg.fill((20, 20, 80))  # Darker blue for menu
    
    try:
        heartImg = pygame.image.load('assets/heart.png')
    except:
        heartImg = pygame.Surface((20, 20))
        heartImg.fill((255, 0, 0))  # Red heart
    
    try:
        playerImg = pygame.image.load('assets/red.png')
    except:
        playerImg = pygame.Surface((64, 64))
        playerImg.fill((255, 0, 0))  # Red player
    
    # Create procedural bullet with glow effect
    bulletImg = pygame.Surface((8, 20), pygame.SRCALPHA)
    # Draw glowing bullet
    pygame.draw.rect(bulletImg, (255, 255, 100), (2, 0, 4, 20))  # Core
    pygame.draw.rect(bulletImg, (255, 255, 0), (1, 2, 6, 16))  # Glow
    pygame.draw.rect(bulletImg, (255, 200, 0), (0, 4, 8, 12))  # Outer glow
    
    # Initialize enemies
    for i in range(num_of_enemies):
        try:
            enemyImg.append(pygame.image.load('assets/enemy1.png'))
        except:
            enemy_surf = pygame.Surface((64, 64))
            enemy_surf.fill((0, 255, 0))  # Green enemy
            enemyImg.append(enemy_surf)
        
        enemyX.append(random.randint(0, 736))
        enemyY.append(random.randint(50, 150))
        enemyX_change.append(2)
        enemyY_change.append(40)
        enemy_spawn_alpha.append(255)  # Initialize spawn animation
    
    # Initialize font
    try:
        font = pygame.font.Font('assets/freesansbold.ttf', 32)
    except:
        font = pygame.font.Font(None, 32)
    
    clock = pygame.time.Clock()

def draw_text(text, font_obj, color, surface, x, y, center=False):
    text_obj = font_obj.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)
    return text_rect

def create_explosion(x, y, color=(255, 150, 0)):
    """Create explosion particles"""
    for _ in range(20):
        angle = random.uniform(0, 2 * 3.14159)
        speed = random.uniform(1, 5)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        size = random.randint(2, 6)
        lifetime = random.randint(20, 40)
        particles.append(Particle(x, y, vx, vy, color, size, lifetime))

def screen_shake(intensity=10, duration=10):
    """Trigger screen shake effect"""
    global screen_shake_intensity, screen_shake_duration
    screen_shake_intensity = max(screen_shake_intensity, intensity)
    screen_shake_duration = max(screen_shake_duration, duration)

def get_shake_offset():
    """Get current shake offset"""
    global screen_shake_intensity, screen_shake_duration
    if screen_shake_duration > 0:
        offset_x = random.randint(-screen_shake_intensity, screen_shake_intensity)
        offset_y = random.randint(-screen_shake_intensity, screen_shake_intensity)
        screen_shake_duration -= 1
        if screen_shake_duration == 0:
            screen_shake_intensity = 0
        return offset_x, offset_y
    return 0, 0

def spawn_powerup(x, y):
    """Randomly spawn a power-up"""
    if random.random() < 0.3:  # 30% chance
        powerup_type = random.choice(["multi_shot", "shield", "slow_motion", "rapid_fire"])
        powerups.append(PowerUp(x, y, powerup_type))

def activate_powerup(powerup_type):
    """Activate a power-up"""
    global active_powerups, powerup_timers
    duration = 300  # 5 seconds at 60 FPS
    active_powerups[powerup_type] = True
    powerup_timers[powerup_type] = duration
    
def update_powerups():
    """Update active power-up timers"""
    global multi_shot_active, shield_active, slow_motion_active, rapid_fire_active
    global active_powerups, powerup_timers, invincible
    
    for powerup_type in list(powerup_timers.keys()):
        powerup_timers[powerup_type] -= 1
        if powerup_timers[powerup_type] <= 0:
            active_powerups[powerup_type] = False
            del powerup_timers[powerup_type]
    
    multi_shot_active = active_powerups.get("multi_shot", False)
    rapid_fire_active = active_powerups.get("rapid_fire", False)
    slow_motion_active = active_powerups.get("slow_motion", False)
    shield_active = active_powerups.get("shield", False)
    
    # Shield provides invincibility
    if shield_active:
        invincible = True

def handle_menu_events():
    global game_state, running, previous_state, show_tutorial
    mx, my = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Play button area
            if 300 <= mx <= 500 and 280 <= my <= 340:
                if show_tutorial:
                    game_state = "tutorial"
                else:
                    game_state = "playing"
                    reset_game()
                # Ensure music is playing when game starts
                if not mixer.music.get_busy():
                    try:
                        mixer.music.play(-1)
                    except:
                        pass
            # Settings button area
            elif 300 <= mx <= 500 and 360 <= my <= 420:
                previous_state = "menu"
                game_state = "settings"
            # Quit button area
            elif 300 <= mx <= 500 and 440 <= my <= 500:
                running = False

def handle_game_events():
    global running, playerX_change, bulletX, bulletY, bullet_state, game_state, show_fps, previous_state
    global input_buffer, rapid_fire_cooldown
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                previous_state = "playing"
                game_state = "paused"
            elif event.key == pygame.K_F3:
                show_fps = not show_fps
            elif event.key == pygame.K_LEFT:
                playerX_change = -7 if rapid_fire_active else -5
            elif event.key == pygame.K_RIGHT:
                playerX_change = 7 if rapid_fire_active else 5
            elif event.key == pygame.K_SPACE:
                # Add to input buffer for smoother shooting
                input_buffer.append(("shoot", buffer_time))
            elif event.key == pygame.K_m:  # Toggle music with 'M' key
                if mixer.music.get_busy():
                    mixer.music.pause()
                else:
                    mixer.music.unpause()
        elif event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                playerX_change = 0
    
    # Process input buffer
    for i, (action, remaining_time) in enumerate(input_buffer):
        if action == "shoot" and bullet_state == "ready":
            if rapid_fire_active:
                if rapid_fire_cooldown <= 0:
                    fire_bullets()
                    rapid_fire_cooldown = 5  # Faster cooldown
                    input_buffer.pop(i)
                    break
            else:
                fire_bullets()
                input_buffer.pop(i)
                break
    
    # Update buffer timers
    input_buffer = [(action, time - 1) for action, time in input_buffer if time > 0]
    
    if rapid_fire_cooldown > 0:
        rapid_fire_cooldown -= 1

def handle_gameover_events():
    global game_state, running
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Restart button area
            if 300 <= mx <= 500 and 280 <= my <= 340:
                game_state = "playing"
                reset_game()
                # Restart music when restarting game
                if not mixer.music.get_busy():
                    try:
                        mixer.music.play(-1)
                    except:
                        pass
            # Quit button area
            elif 300 <= mx <= 500 and 360 <= my <= 420:
                running = False

def handle_paused_events():
    global game_state, running, previous_state
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state = previous_state
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Resume button
            if 300 <= mx <= 500 and 240 <= my <= 290:
                game_state = previous_state
            # Settings button
            elif 300 <= mx <= 500 and 310 <= my <= 360:
                previous_state = "playing"
                game_state = "settings"
            # Main Menu button
            elif 300 <= mx <= 500 and 380 <= my <= 430:
                game_state = "menu"

def handle_settings_events():
    global game_state, running, volume_music, volume_sfx, difficulty, previous_state
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state = previous_state if previous_state else "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Music volume slider
            if 250 <= mx <= 550 and 180 <= my <= 200:
                volume_music = (mx - 250) / 300
                mixer.music.set_volume(volume_music)
            # SFX volume slider
            elif 250 <= mx <= 550 and 240 <= my <= 260:
                volume_sfx = (mx - 250) / 300
            # Difficulty buttons
            elif 250 <= mx <= 350 and 300 <= my <= 340:
                difficulty = "easy"
            elif 360 <= mx <= 460 and 300 <= my <= 340:
                difficulty = "normal"
            elif 470 <= mx <= 570 and 300 <= my <= 340:
                difficulty = "hard"
            # Back button - FIXED HITBOX
            elif 300 <= mx <= 500 and 540 <= my <= 580:
                game_state = previous_state if previous_state else "menu"

def handle_tutorial_events():
    global game_state, running, show_tutorial
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            show_tutorial = False
            game_state = "playing"

def draw_menu():
    screen.blit(menu_bg, (0, 0))
    
    # Semi-transparent overlay
    overlay = pygame.Surface((800, 600))
    overlay.set_alpha(100)
    overlay.fill((0, 0, 20))
    screen.blit(overlay, (0, 0))
    
    mx, my = pygame.mouse.get_pos()
    
    # Title - clean and crisp without glow
    title_font = pygame.font.Font(None, 80)
    draw_text("ASTRO SIEGE", title_font, (255, 255, 150), screen, 400, 140, center=True)
    
    # Subtitle with style
    small_font = pygame.font.Font(None, 26)
    draw_text("by G1 Games", small_font, (150, 200, 255), screen, 400, 215, center=True)
    
    # Decorative stars
    for x, y in [(300, 120), (500, 120), (280, 190), (520, 190)]:
        pygame.draw.circle(screen, (255, 255, 200, 100), (x, y), 3)
    
    # Modern buttons with better icons
    button_font = pygame.font.Font(None, 48)
    
    # Play button
    play_rect = pygame.Rect(300, 280, 200, 60)
    is_play_hover = play_rect.collidepoint(mx, my)
    if is_play_hover:
        pygame.draw.rect(screen, (100, 255, 100), play_rect.inflate(6, 6), border_radius=15)
        pygame.draw.rect(screen, (50, 200, 50), play_rect, border_radius=12)
        draw_text("▶  PLAY", button_font, (255, 255, 255), screen, 400, 310, center=True)
    else:
        pygame.draw.rect(screen, (100, 255, 100), play_rect, 3, border_radius=12)
        pygame.draw.rect(screen, (30, 80, 30), play_rect.inflate(-6, -6), border_radius=10)
        draw_text("▶  PLAY", button_font, (100, 255, 100), screen, 400, 310, center=True)
    
    # Settings button
    settings_rect = pygame.Rect(300, 360, 200, 60)
    is_settings_hover = settings_rect.collidepoint(mx, my)
    if is_settings_hover:
        pygame.draw.rect(screen, (100, 200, 255), settings_rect.inflate(6, 6), border_radius=15)
        pygame.draw.rect(screen, (50, 100, 200), settings_rect, border_radius=12)
        draw_text("⚙  SETTINGS", button_font, (255, 255, 255), screen, 400, 390, center=True)
    else:
        pygame.draw.rect(screen, (100, 200, 255), settings_rect, 3, border_radius=12)
        pygame.draw.rect(screen, (30, 50, 80), settings_rect.inflate(-6, -6), border_radius=10)
        draw_text("⚙  SETTINGS", button_font, (100, 200, 255), screen, 400, 390, center=True)
    
    # Quit button
    quit_rect = pygame.Rect(300, 440, 200, 60)
    is_quit_hover = quit_rect.collidepoint(mx, my)
    if is_quit_hover:
        pygame.draw.rect(screen, (255, 100, 100), quit_rect.inflate(6, 6), border_radius=15)
        pygame.draw.rect(screen, (200, 50, 50), quit_rect, border_radius=12)
        draw_text("✖  QUIT", button_font, (255, 255, 255), screen, 400, 470, center=True)
    else:
        pygame.draw.rect(screen, (255, 100, 100), quit_rect, 3, border_radius=12)
        pygame.draw.rect(screen, (80, 30, 30), quit_rect.inflate(-6, -6), border_radius=10)
        draw_text("✖  QUIT", button_font, (255, 100, 100), screen, 400, 470, center=True)
    
    # Version info
    tiny_font = pygame.font.Font(None, 18)
    draw_text("v1.0 - Enhanced Edition", tiny_font, (100, 100, 150), screen, 400, 570, center=True)

def draw_game():
    global playerX, bulletY, bullet_state, lives, game_state, invincible, invincible_timer, damage_flash_timer
    global particles, powerups, score_popups, bullet_trails, bg_scroll_y, enemy_spawn_alpha
    
    # Get shake offset
    shake_x, shake_y = get_shake_offset()
    
    # Background with parallax scrolling
    screen.fill((0, 0, 0))
    bg_scroll_y += bg_scroll_speed * (0.5 if slow_motion_active else 1.0)
    if bg_scroll_y >= 600:
        bg_scroll_y = 0
    
    # Draw scrolling background twice for seamless loop
    screen.blit(background, (shake_x, int(bg_scroll_y) + shake_y))
    screen.blit(background, (shake_x, int(bg_scroll_y) - 600 + shake_y))
    
    # Damage flash effect
    if damage_flash_timer > 0:
        flash_overlay = pygame.Surface((800, 600))
        flash_overlay.set_alpha(int(damage_flash_timer * 25))
        flash_overlay.fill((255, 0, 0))
        screen.blit(flash_overlay, (0, 0))
        damage_flash_timer -= 1
    
    # Slow motion overlay
    if slow_motion_active:
        slow_overlay = pygame.Surface((800, 600))
        slow_overlay.set_alpha(30)
        slow_overlay.fill((100, 100, 255))
        screen.blit(slow_overlay, (0, 0))
    
    # Player movement
    playerX += playerX_change
    if playerX <= 0:
        playerX = 0
    elif playerX >= 736:
        playerX = 736
    
    # Update invincibility
    if invincible_timer > 0:
        invincible_timer -= 1
        invincible = True
    elif not shield_active:
        invincible = False
    
    # Update power-ups
    update_powerups()
    
    time_scale = 0.5 if slow_motion_active else 1.0
    
    # Update and draw power-ups
    for powerup in powerups[:]:
        if not powerup.update():
            powerups.remove(powerup)
        elif powerup.collides_with(playerX, playerY):
            activate_powerup(powerup.type)
            powerups.remove(powerup)
            create_explosion(powerup.x + 16, powerup.y + 16, powerup.color)
            try:
                pickupSound = mixer.Sound("assets/explosion.wav")
                pickupSound.set_volume(volume_sfx * 0.5)
                pickupSound.play()
            except:
                pass
        else:
            powerup.draw(screen)
    
    # Enemy movement and collision
    for i in range(num_of_enemies):
        enemyX[i] += enemyX_change[i] * time_scale
        if enemyX[i] <= 0:
            enemyX_change[i] = abs(enemyX_change[i])
            enemyY[i] += enemyY_change[i] * time_scale
        elif enemyX[i] >= 736:
            enemyX_change[i] = -abs(enemyX_change[i])
            enemyY[i] += enemyY_change[i] * time_scale
        
        # Check collision with bullet
        if isCollision(enemyX[i], enemyY[i], bulletX, bulletY):
            bulletY = 480
            bullet_state = "ready"
            global score_value
            score_value += 1
            
            # Visual effects
            create_explosion(enemyX[i] + 32, enemyY[i] + 32, (255, 150, 0))
            screen_shake(8, 8)
            score_popups.append(ScorePopup(enemyX[i] + 32, enemyY[i], 1))
            
            # Chance to spawn power-up
            spawn_powerup(enemyX[i], enemyY[i])
            
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)
            enemy_spawn_alpha[i] = 0  # Reset spawn animation
            
            try:
                explosionSound = mixer.Sound("assets/explosion.wav")
                explosionSound.set_volume(volume_sfx)
                explosionSound.play()
            except:
                pass
        
        # Check if enemy reached player
        elif enemyY[i] > playerY - 40 and not invincible:
            lives -= 1
            damage_flash_timer = 10
            invincible_timer = 120
            screen_shake(15, 15)
            create_explosion(playerX + 32, playerY + 32, (255, 50, 50))
            
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)
            enemy_spawn_alpha[i] = 0
            
            if lives <= 0:
                game_state = "game_over"
                # Death animation
                for _ in range(50):
                    create_explosion(playerX + 32 + random.randint(-20, 20), 
                                   playerY + 32 + random.randint(-20, 20), 
                                   (255, 100, 100))
        
        # Draw enemy with spawn animation
        if enemy_spawn_alpha[i] < 255:
            enemy_spawn_alpha[i] = min(255, enemy_spawn_alpha[i] + 5)
        
        enemy_surface = enemyImg[i].copy()
        enemy_surface.set_alpha(enemy_spawn_alpha[i])
        screen.blit(enemy_surface, (int(enemyX[i]) + shake_x, int(enemyY[i]) + shake_y))
    
    # Bullet movement
    if bulletY <= 0:
        bulletY = 480
        bullet_state = "ready"
    if bullet_state == "fire":
        # Add bullet trail (centered)
        bullet_trails.append(BulletTrail(bulletX + 32, bulletY + 10))
        # Center bullet on player (player is 64px wide, bullet is 8px wide)
        screen.blit(bulletImg, (int(bulletX + 28) + shake_x, int(bulletY + 10) + shake_y))
        bulletY -= bulletY_change * (1.5 if rapid_fire_active else 1.0)
    
    # Update and draw bullet trails
    for trail in bullet_trails[:]:
        if not trail.update():
            bullet_trails.remove(trail)
        else:
            trail.draw(screen)
    
    # Draw player (with blinking effect if invincible)
    if not invincible or (invincible_timer // 5) % 2 == 0:
        screen.blit(playerImg, (int(playerX) + shake_x, int(playerY) + shake_y))
        
        # Shield visual effect
        if shield_active:
            shield_size = 80
            shield_surface = pygame.Surface((shield_size * 2, shield_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (100, 200, 255, 100), (shield_size, shield_size), shield_size, 3)
            pygame.draw.circle(shield_surface, (100, 200, 255, 30), (shield_size, shield_size), shield_size)
            screen.blit(shield_surface, (int(playerX + 32 - shield_size) + shake_x, int(playerY + 32 - shield_size) + shake_y))
    
    # Update and draw particles
    for particle in particles[:]:
        if not particle.update():
            particles.remove(particle)
        else:
            particle.draw(screen)
    
    # Update and draw score popups
    for popup in score_popups[:]:
        if not popup.update():
            score_popups.remove(popup)
        else:
            popup.draw(screen)
    
    # Draw UI
    show_score()
    show_lives()
    show_music_status()
    show_active_powerups()
    
    # Show invincibility indicator
    if invincible and not shield_active:
        shield_font = pygame.font.Font(None, 24)
        draw_text("SHIELD ACTIVE", shield_font, (100, 200, 255), screen, 400, 550, center=True)
    
    # Show FPS if enabled
    if show_fps:
        show_fps_counter()

def draw_game_over():
    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    
    # Dark overlay
    overlay = pygame.Surface((800, 600))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    
    mx, my = pygame.mouse.get_pos()
    
    # "GAME OVER" title - clean without glow
    over_font = pygame.font.Font(None, 72)
    draw_text("GAME OVER", over_font, (255, 100, 100), screen, 400, 180, center=True)
    
    # Score panel
    panel_rect = pygame.Rect(250, 250, 300, 80)
    pygame.draw.rect(screen, (50, 50, 70), panel_rect, border_radius=15)
    pygame.draw.rect(screen, (150, 150, 200), panel_rect, 2, border_radius=15)
    
    score_label_font = pygame.font.Font(None, 28)
    score_font = pygame.font.Font(None, 48)
    draw_text("Final Score", score_label_font, (200, 200, 255), screen, 400, 270, center=True)
    draw_text(str(score_value), score_font, (255, 255, 100), screen, 400, 305, center=True)
    
    # Buttons with modern styling
    button_font = pygame.font.Font(None, 40)
    
    # Restart button
    restart_rect = pygame.Rect(300, 360, 200, 50)
    is_restart_hover = restart_rect.collidepoint(mx, my)
    if is_restart_hover:
        pygame.draw.rect(screen, (100, 255, 100), restart_rect.inflate(6, 6), border_radius=12)
        pygame.draw.rect(screen, (50, 200, 50), restart_rect, border_radius=10)
        draw_text("↻  RESTART", button_font, (255, 255, 255), screen, 400, 385, center=True)
    else:
        pygame.draw.rect(screen, (100, 255, 100), restart_rect, 3, border_radius=10)
        pygame.draw.rect(screen, (30, 80, 30), restart_rect.inflate(-6, -6), border_radius=8)
        draw_text("↻  RESTART", button_font, (100, 255, 100), screen, 400, 385, center=True)
    
    # Quit button
    quit_rect = pygame.Rect(300, 430, 200, 50)
    is_quit_hover = quit_rect.collidepoint(mx, my)
    if is_quit_hover:
        pygame.draw.rect(screen, (255, 100, 100), quit_rect.inflate(6, 6), border_radius=12)
        pygame.draw.rect(screen, (200, 50, 50), quit_rect, border_radius=10)
        draw_text("✖  QUIT", button_font, (255, 255, 255), screen, 400, 455, center=True)
    else:
        pygame.draw.rect(screen, (255, 100, 100), quit_rect, 3, border_radius=10)
        pygame.draw.rect(screen, (80, 30, 30), quit_rect.inflate(-6, -6), border_radius=8)
        draw_text("✖  QUIT", button_font, (255, 100, 100), screen, 400, 455, center=True)

def draw_paused():
    # Draw the game state underneath (frozen)
    draw_game()
    
    # Semi-transparent overlay
    overlay = pygame.Surface((800, 600))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 20))
    screen.blit(overlay, (0, 0))
    
    mx, my = pygame.mouse.get_pos()
    
    # Pause title - clean without glow
    pause_font = pygame.font.Font(None, 80)
    draw_text("PAUSED", pause_font, (255, 255, 200), screen, 400, 130, center=True)
    
    # Buttons with modern styling
    button_font = pygame.font.Font(None, 42)
    
    # Resume button
    resume_rect = pygame.Rect(280, 240, 240, 55)
    is_resume_hover = resume_rect.collidepoint(mx, my)
    if is_resume_hover:
        pygame.draw.rect(screen, (100, 255, 100), resume_rect.inflate(6, 6), border_radius=15)
        pygame.draw.rect(screen, (50, 200, 50), resume_rect, border_radius=12)
        draw_text("▶  RESUME", button_font, (255, 255, 255), screen, 400, 267, center=True)
    else:
        pygame.draw.rect(screen, (100, 255, 100), resume_rect, 3, border_radius=12)
        pygame.draw.rect(screen, (30, 80, 30), resume_rect.inflate(-6, -6), border_radius=10)
        draw_text("▶  RESUME", button_font, (100, 255, 100), screen, 400, 267, center=True)
    
    # Settings button
    settings_rect = pygame.Rect(280, 315, 240, 55)
    is_settings_hover = settings_rect.collidepoint(mx, my)
    if is_settings_hover:
        pygame.draw.rect(screen, (100, 200, 255), settings_rect.inflate(6, 6), border_radius=15)
        pygame.draw.rect(screen, (50, 100, 200), settings_rect, border_radius=12)
        draw_text("⚙  SETTINGS", button_font, (255, 255, 255), screen, 400, 342, center=True)
    else:
        pygame.draw.rect(screen, (100, 200, 255), settings_rect, 3, border_radius=12)
        pygame.draw.rect(screen, (30, 50, 80), settings_rect.inflate(-6, -6), border_radius=10)
        draw_text("⚙  SETTINGS", button_font, (100, 200, 255), screen, 400, 342, center=True)
    
    # Main Menu button
    menu_rect = pygame.Rect(280, 390, 240, 55)
    is_menu_hover = menu_rect.collidepoint(mx, my)
    if is_menu_hover:
        pygame.draw.rect(screen, (255, 200, 100), menu_rect.inflate(6, 6), border_radius=15)
        pygame.draw.rect(screen, (200, 150, 50), menu_rect, border_radius=12)
        draw_text("⌂  MAIN MENU", button_font, (255, 255, 255), screen, 400, 417, center=True)
    else:
        pygame.draw.rect(screen, (255, 200, 100), menu_rect, 3, border_radius=12)
        pygame.draw.rect(screen, (80, 60, 20), menu_rect.inflate(-6, -6), border_radius=10)
        draw_text("⌂  MAIN MENU", button_font, (255, 200, 100), screen, 400, 417, center=True)
    
    # Show ESC hint with style
    hint_font = pygame.font.Font(None, 24)
    hint_rect = pygame.Rect(280, 480, 240, 35)
    pygame.draw.rect(screen, (60, 60, 80), hint_rect, border_radius=10)
    draw_text("Press ESC to resume", hint_font, (200, 200, 255), screen, 400, 497, center=True)

def draw_settings():
    screen.fill((0, 0, 0))
    screen.blit(menu_bg, (0, 0))
    
    # Semi-transparent overlay for depth
    overlay = pygame.Surface((800, 600))
    overlay.set_alpha(120)
    overlay.fill((0, 0, 20))
    screen.blit(overlay, (0, 0))
    
    mx, my = pygame.mouse.get_pos()
    
    # Title - clean without glow
    title_font = pygame.font.Font(None, 64)
    draw_text("SETTINGS", title_font, (255, 255, 100), screen, 400, 70, center=True)
    
    # Decorative line under title
    pygame.draw.line(screen, (255, 215, 0), (250, 120), (550, 120), 2)
    
    # Music Volume Section with modern styling
    section_font = pygame.font.Font(None, 30)
    value_font = pygame.font.Font(None, 24)
    
    # Music Volume
    y_pos = 160
    draw_text("♪ Music Volume", section_font, (150, 220, 255), screen, 150, y_pos)
    
    # Slider background with border
    slider_x, slider_y, slider_w, slider_h = 250, y_pos + 5, 300, 20
    pygame.draw.rect(screen, (50, 50, 70), (slider_x - 2, slider_y - 2, slider_w + 4, slider_h + 4), border_radius=12)
    pygame.draw.rect(screen, (30, 30, 50), (slider_x, slider_y, slider_w, slider_h), border_radius=10)
    
    # Filled portion with gradient effect
    filled_width = int(volume_music * slider_w)
    if filled_width > 0:
        for i in range(filled_width):
            color_intensity = 150 + int(105 * (i / slider_w))
            pygame.draw.line(screen, (0, color_intensity, 255), 
                           (slider_x + i, slider_y + 2), 
                           (slider_x + i, slider_y + slider_h - 2))
        pygame.draw.rect(screen, (100, 200, 255), (slider_x, slider_y, filled_width, slider_h), border_radius=10)
    
    # Volume handle
    if filled_width > 0:
        handle_x = slider_x + filled_width
        pygame.draw.circle(screen, (200, 230, 255), (handle_x, slider_y + slider_h//2), 8)
        pygame.draw.circle(screen, (100, 200, 255), (handle_x, slider_y + slider_h//2), 6)
    
    # Percentage with box
    percent_text = f"{int(volume_music * 100)}%"
    percent_bg_rect = pygame.Rect(565, y_pos, 60, 30)
    pygame.draw.rect(screen, (40, 40, 60), percent_bg_rect, border_radius=8)
    draw_text(percent_text, value_font, (150, 220, 255), screen, 595, y_pos + 15, center=True)
    
    # SFX Volume
    y_pos = 220
    draw_text("🔊 SFX Volume", section_font, (255, 150, 150), screen, 150, y_pos)
    
    slider_y = y_pos + 5
    pygame.draw.rect(screen, (70, 50, 50), (slider_x - 2, slider_y - 2, slider_w + 4, slider_h + 4), border_radius=12)
    pygame.draw.rect(screen, (50, 30, 30), (slider_x, slider_y, slider_w, slider_h), border_radius=10)
    
    filled_width = int(volume_sfx * slider_w)
    if filled_width > 0:
        for i in range(filled_width):
            color_intensity = 150 + int(105 * (i / slider_w))
            pygame.draw.line(screen, (color_intensity, 0, 100), 
                           (slider_x + i, slider_y + 2), 
                           (slider_x + i, slider_y + slider_h - 2))
        pygame.draw.rect(screen, (255, 100, 150), (slider_x, slider_y, filled_width, slider_h), border_radius=10)
    
    if filled_width > 0:
        handle_x = slider_x + filled_width
        pygame.draw.circle(screen, (255, 200, 220), (handle_x, slider_y + slider_h//2), 8)
        pygame.draw.circle(screen, (255, 100, 150), (handle_x, slider_y + slider_h//2), 6)
    
    percent_text = f"{int(volume_sfx * 100)}%"
    percent_bg_rect = pygame.Rect(565, y_pos, 60, 30)
    pygame.draw.rect(screen, (60, 40, 40), percent_bg_rect, border_radius=8)
    draw_text(percent_text, value_font, (255, 150, 150), screen, 595, y_pos + 15, center=True)
    
    # Difficulty Section with enhanced buttons
    y_pos = 290
    draw_text("⚔ Difficulty", section_font, (150, 255, 150), screen, 150, y_pos)
    
    button_y = 285
    button_h = 45
    button_font = pygame.font.Font(None, 28)
    
    # Easy button
    easy_rect = pygame.Rect(230, button_y, 110, button_h)
    is_easy_selected = difficulty == "easy"
    is_easy_hover = easy_rect.collidepoint(mx, my)
    
    if is_easy_selected:
        pygame.draw.rect(screen, (100, 255, 100), easy_rect.inflate(4, 4), border_radius=12)
        pygame.draw.rect(screen, (50, 200, 50), easy_rect, border_radius=10)
        draw_text("EASY", button_font, (255, 255, 255), screen, easy_rect.centerx, easy_rect.centery, center=True)
    else:
        border_color = (150, 255, 150) if is_easy_hover else (100, 200, 100)
        bg_color = (40, 80, 40) if is_easy_hover else (30, 60, 30)
        pygame.draw.rect(screen, border_color, easy_rect, 2, border_radius=10)
        pygame.draw.rect(screen, bg_color, easy_rect.inflate(-4, -4), border_radius=8)
        draw_text("EASY", button_font, border_color, screen, easy_rect.centerx, easy_rect.centery, center=True)
    
    # Normal button
    normal_rect = pygame.Rect(350, button_y, 110, button_h)
    is_normal_selected = difficulty == "normal"
    is_normal_hover = normal_rect.collidepoint(mx, my)
    
    if is_normal_selected:
        pygame.draw.rect(screen, (255, 215, 0), normal_rect.inflate(4, 4), border_radius=12)
        pygame.draw.rect(screen, (200, 170, 0), normal_rect, border_radius=10)
        draw_text("NORMAL", button_font, (255, 255, 255), screen, normal_rect.centerx, normal_rect.centery, center=True)
    else:
        border_color = (255, 230, 100) if is_normal_hover else (200, 200, 100)
        bg_color = (80, 80, 40) if is_normal_hover else (60, 60, 30)
        pygame.draw.rect(screen, border_color, normal_rect, 2, border_radius=10)
        pygame.draw.rect(screen, bg_color, normal_rect.inflate(-4, -4), border_radius=8)
        draw_text("NORMAL", button_font, border_color, screen, normal_rect.centerx, normal_rect.centery, center=True)
    
    # Hard button
    hard_rect = pygame.Rect(470, button_y, 110, button_h)
    is_hard_selected = difficulty == "hard"
    is_hard_hover = hard_rect.collidepoint(mx, my)
    
    if is_hard_selected:
        pygame.draw.rect(screen, (255, 100, 100), hard_rect.inflate(4, 4), border_radius=12)
        pygame.draw.rect(screen, (200, 50, 50), hard_rect, border_radius=10)
        draw_text("HARD", button_font, (255, 255, 255), screen, hard_rect.centerx, hard_rect.centery, center=True)
    else:
        border_color = (255, 150, 150) if is_hard_hover else (200, 100, 100)
        bg_color = (80, 40, 40) if is_hard_hover else (60, 30, 30)
        pygame.draw.rect(screen, border_color, hard_rect, 2, border_radius=10)
        pygame.draw.rect(screen, bg_color, hard_rect.inflate(-4, -4), border_radius=8)
        draw_text("HARD", button_font, border_color, screen, hard_rect.centerx, hard_rect.centery, center=True)
    
    # Controls info in a nice panel
    y_pos = 355
    panel_rect = pygame.Rect(150, y_pos, 500, 165)
    pygame.draw.rect(screen, (40, 40, 60), panel_rect, border_radius=15)
    pygame.draw.rect(screen, (100, 100, 150), panel_rect, 2, border_radius=15)
    
    info_font = pygame.font.Font(None, 24)
    label_font = pygame.font.Font(None, 28)
    draw_text("CONTROLS", label_font, (200, 200, 255), screen, 400, y_pos + 22, center=True)
    
    # Draw a separator line
    pygame.draw.line(screen, (80, 80, 120), (180, y_pos + 45), (620, y_pos + 45), 1)
    
    controls = [
        ("←  →", "Move Ship", 60),
        ("SPACE", "Fire Weapon", 95),
        ("ESC", "Pause Game", 130)
    ]
    
    for key, action, y_offset in controls:
        # Key box with consistent styling
        key_rect = pygame.Rect(180, y_pos + y_offset, 100, 30)
        pygame.draw.rect(screen, (60, 60, 90), key_rect, border_radius=8)
        pygame.draw.rect(screen, (150, 150, 200), key_rect, 2, border_radius=8)
        draw_text(key, info_font, (200, 220, 255), screen, key_rect.centerx, key_rect.centery, center=True)
        
        # Action text aligned properly
        draw_text(action, info_font, (180, 180, 220), screen, 300, y_pos + y_offset + 15)
    
    # Additional tips in smaller text
    tip_font = pygame.font.Font(None, 18)
    draw_text("Press M to toggle music  •  F3 for debug info", tip_font, (120, 120, 160), screen, 400, y_pos + 148, center=True)
    
    # Back button with modern design
    back_rect = pygame.Rect(300, 540, 200, 40)
    is_back_hover = back_rect.collidepoint(mx, my)
    
    if is_back_hover:
        pygame.draw.rect(screen, (255, 200, 50), back_rect.inflate(6, 6), border_radius=12)
        pygame.draw.rect(screen, (230, 180, 40), back_rect, border_radius=10)
        draw_text("←  BACK", button_font, (255, 255, 255), screen, back_rect.centerx, back_rect.centery, center=True)
    else:
        pygame.draw.rect(screen, (200, 150, 30), back_rect, 2, border_radius=10)
        pygame.draw.rect(screen, (60, 50, 20), back_rect.inflate(-4, -4), border_radius=8)
        draw_text("←  BACK", button_font, (200, 150, 30), screen, back_rect.centerx, back_rect.centery, center=True)

def draw_tutorial():
    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    
    # Semi-transparent overlay
    overlay = pygame.Surface((800, 600))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 30))
    screen.blit(overlay, (0, 0))
    
    # Title
    title_font = pygame.font.Font(None, 56)
    draw_text("HOW TO PLAY", title_font, (255, 215, 0), screen, 400, 60, center=True)
    
    # Instructions
    info_font = pygame.font.Font(None, 32)
    draw_text("Objective:", info_font, (100, 255, 100), screen, 400, 120, center=True)
    
    small_font = pygame.font.Font(None, 24)
    draw_text("Destroy all enemy ships before they reach you!", small_font, (255, 255, 255), screen, 400, 155, center=True)
    draw_text("Don't let enemies pass or you'll lose a life!", small_font, (255, 200, 200), screen, 400, 180, center=True)
    
    # Controls
    draw_text("Controls:", info_font, (100, 255, 100), screen, 400, 220, center=True)
    draw_text("← → Arrow Keys - Move Ship", small_font, (255, 255, 255), screen, 400, 255, center=True)
    draw_text("SPACE - Fire Bullet", small_font, (255, 255, 255), screen, 400, 280, center=True)
    draw_text("ESC - Pause Game", small_font, (255, 255, 255), screen, 400, 305, center=True)
    draw_text("M - Toggle Music", small_font, (255, 255, 255), screen, 400, 330, center=True)
    
    # Power-ups
    draw_text("Power-Ups:", info_font, (100, 255, 255), screen, 400, 370, center=True)
    tiny_font = pygame.font.Font(None, 20)
    draw_text("Multi-Shot (M) - Fire multiple bullets", tiny_font, (255, 100, 255), screen, 400, 405, center=True)
    draw_text("Shield (S) - Temporary invincibility", tiny_font, (100, 200, 255), screen, 400, 427, center=True)
    draw_text("Slow-Motion (T) - Slows down time", tiny_font, (100, 255, 100), screen, 400, 449, center=True)
    draw_text("Rapid Fire (R) - Faster shooting & movement", tiny_font, (255, 200, 100), screen, 400, 471, center=True)
    
    # Tips
    draw_text("Tips:", info_font, (255, 255, 100), screen, 400, 510, center=True)
    draw_text("• Collect power-ups from destroyed enemies!", small_font, (255, 255, 255), screen, 400, 540, center=True)
    
    # Continue prompt
    prompt_font = pygame.font.Font(None, 28)
    draw_text("Press any key or click to start!", prompt_font, (255, 255, 100), screen, 400, 575, center=True)

def show_score():
    score = font.render("Score : " + str(score_value), True, (255, 255, 255))
    screen.blit(score, (10, 10))

def show_lives():
    small_heart = pygame.transform.scale(heartImg, (20, 20))
    for i in range(lives):
        screen.blit(small_heart, (650 + i * 30, 10))

def show_music_status():
    """Show music status and controls"""
    small_font = pygame.font.Font(None, 20)
    music_text = "Music: ON" if mixer.music.get_busy() else "Music: OFF"
    music_surface = small_font.render(music_text, True, (255, 255, 255))
    screen.blit(music_surface, (10, 50))

def show_fps_counter():
    """Show FPS and debug info"""
    fps_font = pygame.font.Font(None, 24)
    fps = int(clock.get_fps())
    fps_text = fps_font.render(f"FPS: {fps}", True, (0, 255, 0) if fps >= 50 else (255, 255, 0) if fps >= 30 else (255, 0, 0))
    screen.blit(fps_text, (700, 10))
    
    # Additional debug info
    debug_font = pygame.font.Font(None, 18)
    debug_lines = [
        f"Enemies: {num_of_enemies}",
        f"Particles: {len(particles)}",
        f"PowerUps: {len(powerups)}",
        f"Popups: {len(score_popups)}"
    ]
    
    y_offset = 35
    for line in debug_lines:
        debug_text = debug_font.render(line, True, (200, 200, 200))
        screen.blit(debug_text, (700, y_offset))
        y_offset += 18

def apply_transition():
    """Apply fade transition effect"""
    global transition_alpha, transitioning
    
    if transitioning:
        transition_surface = pygame.Surface((800, 600))
        transition_surface.set_alpha(transition_alpha)
        transition_surface.fill((0, 0, 0))
        screen.blit(transition_surface, (0, 0))
        
        transition_alpha += transition_speed
        if transition_alpha >= 255:
            transitioning = False
            transition_alpha = 0

def fire_bullet(x, y):
    global bullet_state
    bullet_state = "fire"

def fire_bullets():
    """Fire bullet(s) based on active power-ups"""
    global bulletX, bulletY, bullet_state
    
    bulletX = playerX
    fire_bullet(bulletX, bulletY)
    
    # Try to play sound
    try:
        bulletSound = mixer.Sound("assets/laser.wav")
        bulletSound.set_volume(volume_sfx)
        bulletSound.play()
    except:
        pass
    
    # Multi-shot fires additional bullets
    if multi_shot_active:
        # TODO: Implement multiple bullets (would need bullet array)
        pass

def show_active_powerups():
    """Display active power-up indicators"""
    x_offset = 10
    y_offset = 100
    small_font = pygame.font.Font(None, 20)
    
    if multi_shot_active:
        time_left = powerup_timers.get("multi_shot", 0) // 60
        draw_text(f"Multi-Shot: {time_left}s", small_font, (255, 100, 255), screen, x_offset, y_offset)
        y_offset += 25
    
    if shield_active:
        time_left = powerup_timers.get("shield", 0) // 60
        draw_text(f"Shield: {time_left}s", small_font, (100, 200, 255), screen, x_offset, y_offset)
        y_offset += 25
    
    if slow_motion_active:
        time_left = powerup_timers.get("slow_motion", 0) // 60
        draw_text(f"Slow-Mo: {time_left}s", small_font, (100, 255, 100), screen, x_offset, y_offset)
        y_offset += 25
    
    if rapid_fire_active:
        time_left = powerup_timers.get("rapid_fire", 0) // 60
        draw_text(f"Rapid Fire: {time_left}s", small_font, (255, 200, 100), screen, x_offset, y_offset)
        y_offset += 25

def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt(math.pow(enemyX - bulletX, 2) + (math.pow(enemyY - bulletY, 2)))
    return distance < 27

def reset_game():
    global playerX, playerX_change, bulletX, bulletY, bullet_state, score_value, lives
    global num_of_enemies, enemyX_change, enemyY_change, invincible, invincible_timer, damage_flash_timer
    global particles, powerups, score_popups, bullet_trails, active_powerups, powerup_timers
    global multi_shot_active, shield_active, slow_motion_active, rapid_fire_active, enemy_spawn_alpha
    global bg_scroll_y, input_buffer, rapid_fire_cooldown
    
    playerX = 370
    playerX_change = 0
    bulletX = 0
    bulletY = 480
    bullet_state = "ready"
    score_value = 0
    lives = max_lives
    invincible = False
    invincible_timer = 0
    damage_flash_timer = 0
    bg_scroll_y = 0
    rapid_fire_cooldown = 0
    
    # Clear all effects
    particles.clear()
    powerups.clear()
    score_popups.clear()
    bullet_trails.clear()
    input_buffer.clear()
    active_powerups.clear()
    powerup_timers.clear()
    
    multi_shot_active = False
    shield_active = False
    slow_motion_active = False
    rapid_fire_active = False
    
    # Apply difficulty settings
    diff_settings = difficulty_settings[difficulty]
    num_of_enemies = diff_settings["starting_enemies"]
    
    # Reset enemies with difficulty-based settings
    enemyX.clear()
    enemyY.clear()
    enemyX_change.clear()
    enemyY_change.clear()
    enemyImg.clear()
    enemy_spawn_alpha.clear()
    
    for i in range(num_of_enemies):
        try:
            enemyImg.append(pygame.image.load('assets/enemy1.png'))
        except:
            enemy_surf = pygame.Surface((64, 64))
            enemy_surf.fill((0, 255, 0))
            enemyImg.append(enemy_surf)
        
        enemyX.append(random.randint(0, 736))
        enemyY.append(random.randint(50, 150))
        enemyX_change.append(diff_settings["enemy_speed"])
        enemyY_change.append(diff_settings["enemy_drop_speed"])
        enemy_spawn_alpha.append(0)  # Start with spawn animation

async def main():
    global running, game_state
    
    await load_assets()
    
    while running:
        if game_state == "menu":
            handle_menu_events()
            draw_menu()
        elif game_state == "tutorial":
            handle_tutorial_events()
            draw_tutorial()
        elif game_state == "playing":
            handle_game_events()
            draw_game()
        elif game_state == "paused":
            handle_paused_events()
            draw_paused()
        elif game_state == "settings":
            handle_settings_events()
            draw_settings()
        elif game_state == "game_over":
            handle_gameover_events()
            draw_game_over()
        
        # Apply transition effect if active
        apply_transition()
        
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)  # Allow other tasks to run
    
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())