import pygame
from sys import exit

# Default parameters
resolution = (800, 600)


class Player:
    __init__(self, c):
        self.position = 0   # The game is effectively cyclical 2D as far as the position.
        self.cycle = c      # It is cyclical but some levels arent so we will set negative values for noncyclical levels
        self.pointList = [[2, 0, 1], [2, 0, 0], [-2, 0, -1]]
        self.movablePoint = 0

    def moveLeft():
        nocyc = 0
        if cycle < 0:
            nocyc = 1
            cycle = cycle * (-1)
        position = position + 1
        if position > cycle:
            position = position - 1
            if nocyc == 0:
                position = 0

    def moveRight():
        nocyc = 0
        if cycle < 0:
            nocyc = 1
            cycle = cycle * (-1)
        position = position - 1
        if position < 0:
            position = position + 1
            if nocyc == 0:
                position = cycle


class Level:
    __init__(self, lvlnum):
        self.levelNumber = lvlnum


def DrawGame(player, level, enemyList):
    option = False
    return option


def DrawMainMenu():
    option = False
    return option


def DrawPauseMenu():
    option = False
    return option


pygame.init()
screen = pygame.display.set_mode(resolution)    # Set Resolution    h,w
pygame.display.set_caption("Another Tempest Clone")     # Sets Name For The Game
clock = pygame.time.Clock()             # Object To Control The Framerate

# base_surface = pygame.Surface(resolution)
screen.fill("black")

while True:
    for event in pygame.event.get():    # Checks for Events From Keyboard Or Mouse
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    DrawGame()
    DrawPauseMenu()
    DrawMainMenu()
    pygame.display.update()
    clock.tick(60)  # 60 Frames/Second
