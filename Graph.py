

class Graph:
    def __init__(self):
        self.nodes = []
        self.nonWalkables = []
        self.fogNodes = []
        self.treeNodes = []
        self.groundNodes = []
        self.swampNodes = []
        self.startNodes = []

    def neighbours(self, node):
        directions = [(-1, -1), (0, -1), (1, -1),
                      (-1, 0), (1, 0),
                      (-1, 1), (0, 1), (1, 1)]
        corners = [(-1, -1), (1, -1),
                   (-1, 1), (1, 1)]
        result = []
        for pos in directions:
            neighbour = [node[0] + pos[0], node[1] + pos[1]]
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
