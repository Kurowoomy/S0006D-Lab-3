import pygame
import Graph

class Parser:
    def __init__(self):
        self.squareDistance = 6
        self.nodePos = {}

    def loadToGraph(self, fileName):
        graph = Graph()
        file = open(fileName, "r+")

        row = file.readline()
        x = 0
        y = 0
        while row != "":
            for symbol in row:
                if symbol != "\n":
                    # add node to nodes
                    graph.nodes.append((x, y))
                    if symbol == "B":
                        graph.nonWalkables.append((x, y))
                    elif symbol == "M":
                        graph.groundNodes.append((x, y))
                        graph.fogNodes.append((x, y))
                    elif symbol == "T":
                        graph.treeNodes.append((x, y))
                    elif symbol == "G":
                        graph.swampNodes.append((x, y))
                    elif symbol == "V":
                        graph.nonWalkables.append((x, y))

                    x += 1
            x = 0
            y += 1
            row = file.readline()

        file.close()

        return graph

    def drawSquares(self, fileName, screen):
        file = open(fileName, "r+")

        row = file.readline()
        x = 0
        y = 0
        posX = 0
        posY = 0
        while row != "":
            for symbol in row:
                if symbol == "X":
                    pygame.draw.rect(screen, (0, 0, 0), [x, y, self.squareSize, self.squareSize])

                if symbol != "\n":  # to access the middle of a square via the position of a node
                    self.nodePos[(posX, posY)] = [x + Graphics.squareSize / 2, y + Graphics.squareSize / 2]
                    posX += 1

                x += self.squareDistance
            x = 0
            posX = 0
            y += self.squareDistance
            posY += 1
            row = file.readline()

        file.close()