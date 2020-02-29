import States
import Enumerations


class Entity:
    def __init__(self, occupation, pos, entityManager, ID):
        self.occupation = occupation
        self.pos = pos
        self.entityManager = entityManager
        self.stateMachine = None
        self.ID = ID
        self.variables = {}
        self.route = None
        self.speed = 0.05  # lower value is faster, 1 is normal speed

    def update(self):
        # upgrade to discoverer if needed
        if self.occupation == "worker" and self.stateMachine.currentState is States.States.lookForTree:

            neighbours = self.entityManager.worldManager.graph.neighbours(self.pos)
            for neighbour in neighbours:

                if neighbour in self.entityManager.worldManager.graph.fogNodes:
                    if self.noOneIsDiscoveringAt(self.pos):
                        self.stateMachine.changeState(States.States.upgradingToDiscoverer)
                        break

        self.stateMachine.update()

    def noOneIsDiscoveringAt(self, node):
        for entity in self.entityManager.entities:
            if entity.pos == node:
                if entity.occupation == "discoverer" or \
                        entity.stateMachine.currentState is States.States.upgradingToDiscoverer:
                    return False
        return True

    def handleMessage(self, telegram):
        if telegram.msg == Enumerations.message_type.isUpgradedDiscoverer:
            self.occupation = "discoverer"
            self.variables["nextFogNode"] = None
            self.stateMachine.changeState(States.States.discover)
        if telegram.msg == Enumerations.message_type.move:
            self.pos = telegram.extraInfo
            if self.occupation == "discoverer":
                self.stateMachine.changeState(States.States.discover)
            else:
                pass

    def move(self, nextNode, graph):
        diagonal = [(-1, -1), (1, -1),
                    (-1, 1), (1, 1)]
        nextNodeInDiagonal = False

        if self.pos in graph.groundNodes and nextNode in graph.groundNodes:
            for node in diagonal:
                if (self.pos[0] + node[0], self.pos[1] + node[1]) == nextNode:
                    self.entityManager.worldManager.messageDispatcher.dispatchMessage\
                        (self, self, Enumerations.message_type.move, 14 * self.speed, nextNode)
                    nextNodeInDiagonal = True
            if not nextNodeInDiagonal:
                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                    (self, self, Enumerations.message_type.move, 10 * self.speed, nextNode)

        elif (self.pos in graph.groundNodes and nextNode in graph.swampNodes) or \
                (self.pos in graph.swampNodes and nextNode in graph.groundNodes):
            for node in diagonal:
                if (self.pos[0] + node[0], self.pos[1] + node[1]) == nextNode:
                    self.entityManager.worldManager.messageDispatcher.dispatchMessage\
                        (self, self, Enumerations.message_type.move, 21 * self.speed, nextNode)
                    nextNodeInDiagonal = True
            if not nextNodeInDiagonal:
                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                    (self, self, Enumerations.message_type.move, 15 * self.speed, nextNode)

        elif self.pos in graph.swampNodes and nextNode in graph.swampNodes:
            for node in diagonal:
                if (self.pos[0] + node[0], self.pos[1] + node[1]) == nextNode:
                    self.entityManager.worldManager.messageDispatcher.dispatchMessage\
                        (self, self, Enumerations.message_type.move, 28 * self.speed, nextNode)
                    nextNodeInDiagonal = True
            if not nextNodeInDiagonal:
                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                    (self, self, Enumerations.message_type.move, 20 * self.speed, nextNode)

        self.stateMachine.changeState(States.States.idle)
