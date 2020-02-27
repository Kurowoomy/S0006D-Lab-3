import pygame
import Parser


pygame.init()
screen = pygame.display.set_mode((1080, 1080))
pygame.display.set_caption("Strategiskt AI")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # drawing-------------------------
    screen.fill((255, 255, 255))

    # draw path

    pygame.display.update()
