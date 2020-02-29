

class Graph:
    def __init__(self):
        self.nodes = []
        self.nonWalkables = []
        self.fogNodes = []
        self.treeNodes = []
        self.groundNodes = []
        self.swampNodes = []
        self.startNodes = []
        self.occupiedNodes = []

    def neighbours(self, node):
        directions = [(-1, -1), (0, -1), (1, -1),
                      (-1, 0), (1, 0),
                      (-1, 1), (0, 1), (1, 1)]
        corners = [(-1, -1), (1, -1),
                   (-1, 1), (1, 1)]
        result = []
        for pos in directions:
            neighbour = (node[0] + pos[0], node[1] + pos[1])
            if neighbour in self.nodes and neighbour not in self.nonWalkables:
                if pos in corners and not self.cornerIsReachable(neighbour, node):
                    pass
                else:
                    result.append(neighbour)  # add only walkable nodes to neighbours

        return result

    def cornerIsReachable(self, corner, node):
        if corner[0] is node[0] - 1 and corner[1] is node[1] - 1:  # upper left
            if [node[0], node[1] - 1] in self.nonWalkables or [node[0] - 1, node[1]] in self.nonWalkables:
                return False
        elif corner[0] is node[0] + 1 and corner[1] is node[1] - 1:  # upper right
            if [node[0], node[1] - 1] in self.nonWalkables or [node[0] + 1, node[1]] in self.nonWalkables:
                return False
        elif corner[0] is node[0] - 1 and corner[1] is node[1] + 1:  # lower left
            if [node[0], node[1] + 1] in self.nonWalkables or [node[0] - 1, node[1]] in self.nonWalkables:
                return False
        elif corner[0] is node[0] + 1 and corner[1] is node[1] + 1:  # lower right
            if [node[0], node[1] + 1] in self.nonWalkables or [node[0] + 1, node[1]] in self.nonWalkables:
                return False
        return True

    def loadToGraph(self, fileName):
        file = open(fileName, "r+")

        row = file.readline()
        x = 0
        y = 0
        while row != "":
            for symbol in row:
                if symbol != "\n":
                    # add node to nodes
                    self.nodes.append((x, y))
                    if symbol == "B":
                        self.nonWalkables.append((x, y))
                    elif symbol == "M":
                        self.groundNodes.append((x, y))
                    elif symbol == "T":
                        self.treeNodes.append((x, y))
                        self.groundNodes.append((x, y))
                    elif symbol == "G":
                        self.swampNodes.append((x, y))
                    elif symbol == "V":
                        self.nonWalkables.append((x, y))

                    x += 1
            x = 0
            y += 1
            row = file.readline()

        file.close()

    def setStartPositions(self, startPos):
        startPositions = [(0, 0), (1, 0), (2, 0),
                          (0, 1), (1, 1), (2, 1),
                          (0, 2), (1, 2), (2, 2)]
        for pos in startPositions:
            posNode = (startPos[0] + pos[0], startPos[1] + pos[1])
            self.startNodes.append(posNode)
            self.fogNodes.remove(posNode)

    def setFog(self):
        for node in self.swampNodes:
            self.fogNodes.append(node)
        for node in self.groundNodes:
            self.fogNodes.append(node)
        for node in self.treeNodes:
            self.fogNodes.append(node)
