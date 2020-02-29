import States
import Enumerations
import Algorithms


class Entity:
    def __init__(self, occupation, pos, entityManager, ID):
        self.occupation = occupation
        self.pos = pos
        self.entityManager = entityManager
        self.stateMachine = None
        self.ID = ID
        self.variables = {}
        self.route = []
        self.speed = 0.05  # lower value is faster, 1 is normal speed
        self.destinationDistance = None

    def update(self):
        # upgrade to discoverer if needed
        if self.occupation == "worker" and self.stateMachine.currentState is States.States.wandering:

            neighbours = self.entityManager.worldManager.graph.neighbours(self.pos)
            for neighbour in neighbours:

                if neighbour in self.entityManager.worldManager.graph.fogNodes:
                    if self.noOneIsDiscoveringAt(self.pos):
                        self.stateMachine.changeState(States.States.upgradingToDiscoverer)
                        break

        self.stateMachine.update()

    def noOneIsDiscoveringAt(self, node):
        for entity in self.entityManager.discoverers:
            if entity.pos == node or entity.pos in self.entityManager.worldManager.graph.neighbours(node):
                return False
        for entity in self.entityManager.isUpgrading:
            if entity.pos == node or entity.pos in self.entityManager.worldManager.graph.neighbours(node):
                return False
        return True

    def handleMessage(self, telegram):
        if telegram.msg == Enumerations.message_type.isUpgradedDiscoverer:
            self.occupation = "discoverer"
            self.entityManager.discoverers.append(self)
            self.entityManager.isUpgrading.remove(self)
            self.entityManager.workers.remove(self)
            self.variables["nextFogNode"] = None
            self.stateMachine.changeState(States.States.discover)

        elif telegram.msg == Enumerations.message_type.move:
            self.pos = telegram.extraInfo
            if self.occupation == "discoverer":
                self.stateMachine.changeState(States.States.discover)
            elif self.occupation == "worker":
                self.stateMachine.changeState(States.States.wandering)

        elif telegram.msg == Enumerations.message_type.treeAppeared:
            # TODO: make worker lookForTree(s?)
            # handle message if currentState is wandering
            if self.stateMachine.currentState is States.States.wandering:
                # check if tree is occupied
                if telegram.extraInfo in self.entityManager.worldManager.graph.occupiedNodes:
                    # if occupied, check if distance is shorter for self
                    distance = Algorithms.heuristic(telegram.extraInfo, self.pos)
                    otherDistance = Algorithms.heuristic\
                        (telegram.extraInfo, self.entityManager.worldManager.trees[telegram.extraInfo].owner.pos)
                        # if shorter for self, change worker of tree to self, changeState(ChopTree)
                    if distance < otherDistance:
                        self.entityManager.worldManager.trees[telegram.extraInfo].owner = self
                        self.stateMachine.changeState(States.States.ChopTree)
                # if not occupied, change worker tree to self, changeState(ChopTree)
                else:
                    self.entityManager.worldManager.trees[telegram.extraInfo].owner = self
                    self.stateMachine.changeState(States.States.ChopTree)

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
