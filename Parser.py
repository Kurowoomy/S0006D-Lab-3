import pygame


class Parser:
    def __init__(self):
        self.squareSize = 10
        self.entitySize = 1
        self.nodePos = {}
        self.treeSize = 4

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
                        pygame.draw.rect(screen, (124, 198, 210), [x, y, self.squareSize, self.squareSize])
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

    def drawEntities(self, worldManager, screen):
        for entity in worldManager.entityManager.entities:
            if entity.occupation == "worker":
                pygame.draw.circle(screen, (255, 0, 0), self.nodePos[entity.pos], self.entitySize)
            if entity.occupation == "discoverer":
                pygame.draw.circle(screen, (0, 0, 255), self.nodePos[entity.pos], self.entitySize)

    def drawFog(self, fogNodes, screen):
        for node in fogNodes:
            x = self.nodePos[node][0] - self.squareSize/2
            y = self.nodePos[node][1] - self.squareSize/2
            pygame.draw.rect(screen, (150, 150, 150), [x, y, self.squareSize, self.squareSize])

    def drawObjects(self, worldManager, screen):
        for tree in worldManager.trees:
            pointList = ((self.nodePos[tree.pos][0], self.nodePos[tree.pos][1] - self.treeSize),
                         (self.nodePos[tree.pos][0] - self.treeSize, self.nodePos[tree.pos][1] + self.treeSize),
                         (self.nodePos[tree.pos][0] + self.treeSize, self.nodePos[tree.pos][1] + self.treeSize))
            pygame.draw.polygon(screen, (47, 96, 64), pointList)
