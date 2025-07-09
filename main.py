import math
import random
import asyncio
import pygame
from pygame.locals import *
from pygame import mixer

print("Game Loaded!")

# Global variables
screen = None
background = None
menu_bg = None
font = None
score_value = 0
lives = 3
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
game_state = "menu"  # "menu", "playing", "game_over"

async def load_assets():
    """Load all game assets"""
    global screen, background, menu_bg, font, heartImg, playerImg, bulletImg, enemyImg, clock
    
    pygame.init()
    mixer.init()  # Initialize mixer for sound
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Astro Siege")
    
    # Load and play background music
    try:
        mixer.music.load("assets/cb.mp3")
        mixer.music.set_volume(0.1)
        mixer.music.play(-1)  # -1 means loop indefinitely
        print("Background music loaded successfully")
    except Exception as e:
        print(f"Could not load background music: {e}")
        # Try alternative file names
        try:
            mixer.music.load("cb.mp3")
            mixer.music.set_volume(0.1)
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
    
    try:
        bulletImg = pygame.image.load('assets/b1.png')
    except:
        bulletImg = pygame.Surface((8, 16))
        bulletImg.fill((255, 255, 0))  # Yellow bullet
    
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

def handle_menu_events():
    global game_state, running
    mx, my = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Play button area
            if 300 <= mx <= 500 and 280 <= my <= 340:
                game_state = "playing"
                reset_game()
                # Ensure music is playing when game starts
                if not mixer.music.get_busy():
                    try:
                        mixer.music.play(-1)
                    except:
                        pass
            # Quit button area
            elif 300 <= mx <= 500 and 360 <= my <= 420:
                running = False

def handle_game_events():
    global running, playerX_change, bulletX, bulletY, bullet_state, game_state
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playerX_change = -5
            elif event.key == pygame.K_RIGHT:
                playerX_change = 5
            elif event.key == pygame.K_SPACE and bullet_state == "ready":
                bulletX = playerX
                fire_bullet(bulletX, bulletY)
                # Try to play sound
                try:
                    bulletSound = mixer.Sound("assets/laser.wav")
                    bulletSound.set_volume(0.5)
                    bulletSound.play()
                except:
                    pass
            elif event.key == pygame.K_m:  # Toggle music with 'M' key
                if mixer.music.get_busy():
                    mixer.music.pause()
                else:
                    mixer.music.unpause()
        elif event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                playerX_change = 0

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

def draw_menu():
    screen.blit(menu_bg, (0, 0))
    
    # Title
    title_font = pygame.font.Font(None, 72)
    draw_text("ASTRO SIEGE", title_font, (255, 215, 0), screen, 400, 150, center=True)
    
    # Subtitle
    small_font = pygame.font.Font(None, 24)
    draw_text("by G1 Games", small_font, (200, 200, 255), screen, 400, 220, center=True)
    
    # Buttons
    mx, my = pygame.mouse.get_pos()
    play_color = (50, 255, 50) if 300 <= mx <= 500 and 280 <= my <= 340 else (180, 255, 180)
    quit_color = (255, 50, 50) if 300 <= mx <= 500 and 360 <= my <= 420 else (255, 180, 180)
    
    menu_font = pygame.font.Font(None, 48)
    draw_text("PLAY", menu_font, play_color, screen, 400, 300, center=True)
    draw_text("QUIT", menu_font, quit_color, screen, 400, 380, center=True)

def draw_game():
    global playerX, bulletY, bullet_state, lives, game_state
    
    # Background
    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    
    # Player movement
    playerX += playerX_change
    if playerX <= 0:
        playerX = 0
    elif playerX >= 736:
        playerX = 736
    
    # Enemy movement
    for i in range(num_of_enemies):
        enemyX[i] += enemyX_change[i]
        if enemyX[i] <= 0:
            enemyX_change[i] = 2
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >= 736:
            enemyX_change[i] = -2
            enemyY[i] += enemyY_change[i]
        
        # Check collision
        if isCollision(enemyX[i], enemyY[i], bulletX, bulletY):
            bulletY = 480
            bullet_state = "ready"
            global score_value
            score_value += 1
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)
            try:
                explosionSound = mixer.Sound("assets/explosion.wav")
                explosionSound.set_volume(0.3)
                explosionSound.play()
            except:
                pass
        
        # Check if enemy reached player
        elif enemyY[i] > playerY - 40:
            lives -= 1
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)
            if lives <= 0:
                game_state = "game_over"
        
        # Draw enemy
        screen.blit(enemyImg[i], (enemyX[i], enemyY[i]))
    
    # Bullet movement
    if bulletY <= 0:
        bulletY = 480
        bullet_state = "ready"
    if bullet_state == "fire":
        screen.blit(bulletImg, (bulletX + 16, bulletY + 10))
        bulletY -= bulletY_change
    
    # Draw player
    screen.blit(playerImg, (playerX, playerY))
    
    # Draw UI
    show_score()
    show_lives()
    show_music_status()

def draw_game_over():
    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    
    over_font = pygame.font.Font(None, 64)
    draw_text("GAME OVER", over_font, (255, 0, 0), screen, 400, 200, center=True)
    
    mx, my = pygame.mouse.get_pos()
    restart_color = (255, 255, 255) if 300 <= mx <= 500 and 280 <= my <= 340 else (180, 180, 180)
    quit_color = (255, 255, 255) if 300 <= mx <= 500 and 360 <= my <= 420 else (180, 180, 180)
    
    small_font = pygame.font.Font(None, 32)
    draw_text("RESTART", small_font, restart_color, screen, 400, 300, center=True)
    draw_text("QUIT", small_font, quit_color, screen, 400, 360, center=True)

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
    
    control_text = small_font.render("Press 'M' to toggle music", True, (180, 180, 180))
    screen.blit(control_text, (10, 70))

def fire_bullet(x, y):
    global bullet_state
    bullet_state = "fire"

def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt(math.pow(enemyX - bulletX, 2) + (math.pow(enemyY - bulletY, 2)))
    return distance < 27

def reset_game():
    global playerX, playerX_change, bulletX, bulletY, bullet_state, score_value, lives
    playerX = 370
    playerX_change = 0
    bulletX = 0
    bulletY = 480
    bullet_state = "ready"
    score_value = 0
    lives = 3
    for i in range(num_of_enemies):
        enemyX[i] = random.randint(0, 736)
        enemyY[i] = random.randint(50, 150)

async def main():
    global running, game_state
    
    await load_assets()
    
    while running:
        if game_state == "menu":
            handle_menu_events()
            draw_menu()
        elif game_state == "playing":
            handle_game_events()
            draw_game()
        elif game_state == "game_over":
            handle_gameover_events()
            draw_game_over()
        
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)  # Allow other tasks to run
    
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())