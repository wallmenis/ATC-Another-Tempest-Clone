import pygame
from sys import exit

pygame.init()

screen = pygame.display.set_mode((800, 600)) #Set Resolution
pygame.display.set_caption("Another Tempest Clone") #Sets Name For The Game
clock = pygame.time.Clock() #Object To Control The Framerate

surface = pygame.Surface((100, 200))
surface.fill('Green')

while True:
    for event in pygame.event.get(): #Checks for Events From Keyboard Or Mouse
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    # draw all our elements
    # update everything
    
    screen.blit(surface,(100, 0))
            
    pygame.display.update()
    clock.tick(60)  #60FPS/Second
