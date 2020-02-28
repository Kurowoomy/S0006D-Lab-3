import pygame


class Parser:
    def __init__(self):
        self.squareSize = 10
        self.entitySize = 5
        self.nodePos = {}

    def drawMap(self, fileName, screen):
        file = open(fileName, "r+")

        row = file.readline()
        x = 0
        y = 0
        posX = 0
        posY = 0
        while row != "":
            for symbol in row:
                if symbol != "\n":  # to access the middle of a square via the position of a node
                    if symbol == "B":
                        pygame.draw.rect(screen, (23, 33, 33), [x, y, self.squareSize, self.squareSize])
                    if symbol == "M" or symbol == "T":
                        pygame.draw.rect(screen, (143, 227, 135), [x, y, self.squareSize, self.squareSize])
                    if symbol == "V":
                        pygame.draw.rect(screen, (74, 182, 191), [x, y, self.squareSize, self.squareSize])
                    if symbol == "G":
                        pygame.draw.rect(screen, (105, 166, 100), [x, y, self.squareSize, self.squareSize])

                    self.nodePos[(posX, posY)] = (int(x + self.squareSize / 2), int(y + self.squareSize / 2))
                    posX += 1

                x += self.squareSize
            x = 0
            posX = 0
            y += self.squareSize
            posY += 1
            row = file.readline()

        file.close()

    def drawEntities(self, entities, screen):
        for entity in entities:
            if entity.occupation == "worker":
                pygame.draw.circle(screen, (255, 0, 0), self.nodePos[entity.pos], 5)

    def drawFog(self, fogNodes, screen):
        for node in fogNodes:  # TODO: fixa positionen av dimman, hamnar i mitten av rutan pga nodePos
            pygame.draw.rect(screen, (230, 230, 230), [self.nodePos[node][0], self.nodePos[node][1], self.squareSize, self.squareSize])
