import math
import random

from pygame.locals import *
import pygame
from pygame import mixer

pygame.init()
screen = pygame.display.set_mode((800, 600))
background = pygame.image.load('background.png')
menu_bg = pygame.image.load('bg1.png') 

mixer.music.load("cb.mp3")
mixer.music.set_volume(0.1)
mixer.music.play(-1)

pygame.display.set_caption("Astro Siege")
icon = pygame.image.load('g1.png')
pygame.display.set_icon(icon)

font = pygame.font.Font('freesansbold.ttf', 32)

score_value = 0
lives = 3
heartImg = pygame.image.load('heart.png')

playerImg = pygame.image.load('red.png')
playerX = 370
playerY = 480
playerX_change = 0

bulletImg = pygame.image.load('b1.png')
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
for i in range(num_of_enemies):
    enemyImg.append(pygame.image.load('enemy1.png'))
    enemyX.append(random.randint(0, 736))
    enemyY.append(random.randint(50, 150))
    enemyX_change.append(2)
    enemyY_change.append(40)

clock = pygame.time.Clock()

def draw_text(text, font, color, surface, x, y, center=False):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)
    return text_rect

def show_menu():
    menu_font = pygame.font.SysFont('comicsansms', 48, bold=True)
    small_font = pygame.font.SysFont('arial', 24, italic=True)
    title_font = pygame.font.SysFont('impact', 72)

    while True:
        screen.blit(menu_bg, (0, 0))

        draw_text("ASTRO SIEGE", title_font, (255, 215, 0), screen, 400, 150, center=True)
        draw_text("by G1 Games", small_font, (200, 200, 255), screen, 400, 220, center=True)

        mx, my = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        # Temporary invisible button rects for hover detection
        play_btn_rect = pygame.Rect(300, 280, 200, 60)  # x, y, width, height
        quit_btn_rect = pygame.Rect(300, 360, 200, 60)

        play_color = (50, 255, 50) if play_btn_rect.collidepoint((mx, my)) else (180, 255, 180)
        quit_color = (255, 50, 50) if quit_btn_rect.collidepoint((mx, my)) else (255, 180, 180)

        play_btn = draw_text("PLAY", menu_font, play_color, screen, 400, 300, center=True)
        quit_btn = draw_text("QUIT", menu_font, quit_color, screen, 400, 380, center=True)

        if play_btn.collidepoint((mx, my)) and click[0]:
            break

        if quit_btn.collidepoint((mx, my)) and click[0]:
            pygame.quit()
            exit()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.display.update()
        clock.tick(60)


def show_game_over():
    over_font = pygame.font.Font('freesansbold.ttf', 64)
    small_font = pygame.font.Font('freesansbold.ttf', 32)
    while True:
        screen.fill((0, 0, 0))
        screen.blit(background, (0, 0))

        draw_text("GAME OVER", over_font, (255, 0, 0), screen, 400, 200, center=True)
        restart_btn = draw_text("RESTART", small_font, (255, 255, 255), screen, 400, 300, center=True)
        quit_btn = draw_text("QUIT", small_font, (255, 255, 255), screen, 400, 360, center=True)

        mx, my = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if restart_btn.collidepoint((mx, my)) and click[0]:
            main_game()
            break

        if quit_btn.collidepoint((mx, my)) and click[0]:
            pygame.quit()
            exit()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.display.update()
        clock.tick(60)

def player(x, y):
    screen.blit(playerImg, (x, y))

def enemy(x, y, i):
    screen.blit(enemyImg[i], (x, y))

def show_score():
    score = font.render("Score : " + str(score_value), True, (255, 255, 255))
    screen.blit(score, (10, 10))

def show_lives():
    small_heart = pygame.transform.scale(heartImg, (20, 20))
    for i in range(lives):
        screen.blit(small_heart, (650 + i * 30, 10))

def fire_bullet(x, y):
    global bullet_state
    bullet_state = "fire"
    screen.blit(bulletImg, (x + 16, y + 10))

def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt(math.pow(enemyX - bulletX, 2) + (math.pow(enemyY - bulletY, 2)))
    return distance < 27

def set_background():
    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))

def move_bullet():
    global bulletY, bullet_state
    if bulletY <= 0:
        bulletY = 480
        bullet_state = "ready"
    if bullet_state == "fire":
        fire_bullet(bulletX, bulletY)
        bulletY -= bulletY_change

def game_input():
    global running, playerX_change, bulletX, bulletY, bullet_state
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playerX_change = -5
            if event.key == pygame.K_RIGHT:
                playerX_change = 5
            if event.key == pygame.K_SPACE and bullet_state == "ready":
                bulletX = playerX
                fire_bullet(bulletX, bulletY)
                bulletSound = mixer.Sound("laser.wav")
                bulletSound.set_volume(0.5)
                bulletSound.play()

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                playerX_change = 0

def enemy_movement():
    for i in range(num_of_enemies):
        enemyX[i] += enemyX_change[i]
        if enemyX[i] <= 0:
            enemyX_change[i] = 2
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >= 736:
            enemyX_change[i] = -2
            enemyY[i] += enemyY_change[i]
        enemy(enemyX[i], enemyY[i], i)

def collision():
    global bulletY, bullet_state, score_value, lives, running
    for i in range(num_of_enemies):
        if isCollision(enemyX[i], enemyY[i], bulletX, bulletY):
            bulletY = 480
            bullet_state = "ready"
            score_value += 1
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)
            explosionSound = mixer.Sound("explosion.wav")
            explosionSound.set_volume(0.3)
            explosionSound.play()

        elif enemyY[i] > playerY - 40:
            lives -= 1
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)
            if lives <= 0:
                running = False

def main_game():
    global running, playerX, playerX_change, bulletX, bulletY, bullet_state, score_value, lives
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

    running = True
    while running:
        set_background()
        game_input()
        playerX += playerX_change
        enemy_movement()
        collision()
        move_bullet()
        player(playerX, playerY)
        show_score()
        show_lives()
        pygame.display.update()
        clock.tick(60)

    show_game_over()

show_menu()
main_game()
