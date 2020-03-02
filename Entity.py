import States
import Enumerations
import Algorithms
import Objects


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
        self.destination = []  # [0] is (x, y), [1] is location_type
        self.isWorking = False
        # TODO: skapa kilnManager
        # TODO: fixa variabel för trädet worker:n har fält så den kan för det till närmaste kilnManager

    def update(self):
        # upgrade to discoverer if needed
        if self.occupation == "worker" and self.stateMachine.currentState is States.States.wandering and \
                self.entityManager.worldManager.needDiscoverers:

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
            self.variables.popitem()
            self.variables["nextFogNode"] = None
            if len(self.entityManager.discoverers) >= 20:
                self.entityManager.worldManager.needDiscoverers = False

            self.stateMachine.changeState(States.States.discover)

        elif telegram.msg == Enumerations.message_type.move:
            self.pos = telegram.extraInfo

            if self.occupation == "discoverer":
                self.stateMachine.changeState(States.States.discover)

            elif self.occupation == "worker" and not self.isWorking:
                self.stateMachine.changeState(States.States.wandering)

            elif self.occupation == "worker" and self.isWorking:
                if self.pos == self.destination[0] and self.destination[1] == Enumerations.location_type.tree:
                    self.stateMachine.changeState(States.States.chopTree)
                else:
                    self.stateMachine.changeState(States.States.moveToDestination)

            elif self.occupation == "builder":
                if self.isWorking and self.pos == self.destination[0] and \
                        self.destination[1] == Enumerations.location_type.kiln:
                    self.stateMachine.changeState(States.States.build)
                elif self.isWorking:
                    self.stateMachine.changeState(States.States.moveToDestination)
                else:
                    self.stateMachine.changeState(States.States.idle)

            elif self.occupation == "kilnManager":
                if self.isWorking:
                    self.stateMachine.changeState(States.States.moveToDestination)
                else:
                    self.stateMachine.changeState(States.States.idle)

        elif telegram.msg == Enumerations.message_type.treeAppeared:
            # handle message if this entity wants a tree to chop
            if not self.isWorking and self.variables["item"] is None:
                # check if tree has owner
                if self.entityManager.worldManager.trees[telegram.extraInfo].owner is not None:
                    # if occupied, check if distance is shorter for self
                    distance = Algorithms.heuristic(telegram.extraInfo, self.pos)
                    otherDistance = Algorithms.heuristic \
                        (telegram.extraInfo, self.entityManager.worldManager.trees[telegram.extraInfo].owner.pos)
                    # if shorter for self, change worker of tree to self, changeState(ChopTree)
                    if distance < otherDistance:
                        # make previous owner change state to wandering
                        self.entityManager.worldManager.trees[telegram.extraInfo].owner.destination.pop(0)
                        self.entityManager.worldManager.trees[telegram.extraInfo].owner.destination.pop(0)
                        self.entityManager.worldManager.trees[telegram.extraInfo].owner.route.clear()
                        self.entityManager.worldManager.trees[telegram.extraInfo].owner. \
                            stateMachine.changeState(States.States.wandering)

                        self.entityManager.worldManager.trees[telegram.extraInfo].owner = self
                        self.destination.append(telegram.extraInfo)
                        self.destination.append(Enumerations.location_type.tree)
                        self.stateMachine.changeState(States.States.chopTree)

                # if not occupied, change worker tree to self, changeState(ChopTree)
                else:
                    self.entityManager.worldManager.trees[telegram.extraInfo].owner = self
                    # change destination to tree
                    self.destination.append(telegram.extraInfo)
                    self.destination.append(Enumerations.location_type.tree)
                    self.stateMachine.changeState(States.States.chopTree)

        elif telegram.msg == Enumerations.message_type.treeIsChopped:
            self.entityManager.worldManager.gatheredTreesAvailable += 1
            self.variables["item"] = self.entityManager.worldManager.trees[self.pos]
            if self.entityManager.worldManager.gatheredTreesAvailable >= 10 and \
                    len(self.entityManager.builders) >= 0 and self.entityManager.worldManager.needKiln:
                for builder in self.entityManager.builders:
                    if not builder.isWorking:
                        self.entityManager.worldManager.needKiln = False
                        builder.stateMachine.changeState(States.States.build)

            self.entityManager.worldManager.trees.pop(self.pos, telegram.extraInfo)
            self.entityManager.worldManager.graph.freeGroundNodes.append(self.pos)
            newTree = self.entityManager.worldManager.addNewTree()
            if newTree.pos in self.entityManager.worldManager.graph.freeGroundNodes:
                self.entityManager.worldManager.graph.freeGroundNodes.remove(newTree.pos)

            if newTree.pos not in self.entityManager.worldManager.graph.fogNodes:
                for entity in self.entityManager.workers:
                    if entity not in self.entityManager.isUpgrading:
                        self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                            (entity, self, Enumerations.message_type.treeAppeared, 0, newTree.pos)

            # start carrying tree if has destination
            if len(self.destination) <= 0:
                self.stateMachine.changeState(States.States.wandering)
            else:
                self.stateMachine.changeState(States.States.carryTree)

        elif telegram.msg == Enumerations.message_type.isUpgradedBuilder:
            self.occupation = "builder"
            self.entityManager.builders.append(self)
            self.entityManager.isUpgrading.remove(self)
            self.entityManager.workers.remove(self)
            # add eventual variables here
            self.entityManager.worldManager.needBuilders = False
            self.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, self)
            self.route.clear()
            self.isWorking = False
            if len(self.destination) > 0:
                self.destination.pop(0)
                self.destination.pop(0)
            # remove variable
            self.variables.popitem()

            self.stateMachine.changeState(States.States.idle)

        elif telegram.msg == Enumerations.message_type.buildingIsDone:
            self.entityManager.worldManager.buildings[self.pos] = Objects.Kiln(self.pos)
            self.entityManager.worldManager.graph.freeGroundNodes.remove(self.pos)

            self.isWorking = False
            # tell a free kilnManager that it can start moving to self.pos
            for entity in self.entityManager.kilnManagers:
                if not entity.isWorking:
                    entity.destination.append(self.pos)
                    entity.destination.append(Enumerations.location_type.kiln)
                    entity.stateMachine.changeState(States.States.manageKiln)
                    break

            neighbours = self.entityManager.worldManager.graph.neighboursExceptFog(self.pos)
            self.move(neighbours[0], self.entityManager.worldManager.graph)

        elif telegram.msg == Enumerations.message_type.isUpgradedKilnManager:
            self.occupation = "kilnManager"
            self.entityManager.kilnManagers.append(self)
            self.entityManager.isUpgrading.remove(self)
            self.entityManager.workers.remove(self)
            # add eventual variables here
            self.variables.popitem()
            self.variables["items"] = []
            self.variables["isMakingCharcoal"] = False

            self.entityManager.worldManager.needKilnManager = False
            self.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, self)
            self.route.clear()
            self.isWorking = False
            if len(self.destination) > 0:
                self.destination.pop(0)
                self.destination.pop(0)
            self.stateMachine.changeState(States.States.idle)

        elif telegram.msg == Enumerations.message_type.charcoalIsDone:
            self.entityManager.worldManager.charcoal += 1
            self.variables["items"].pop(0)
            self.variables["items"].pop(0)
            if self.entityManager.worldManager.charcoal >= 20:
                print("20 charcoal has been made! :D Betyg 3 är nått!")

            self.variables["isMakingCharcoal"] = False
            # tell a free kilnManager that it can start moving to self.pos
            for entity in self.entityManager.kilnManagers:
                if not entity.isWorking:
                    entity.destination[self.pos] = Enumerations.location_type.kiln
                    entity.stateMachine.changeState(States.States.manageKiln)
                    break

    def move(self, nextNode, graph):
        diagonal = [(-1, -1), (1, -1),
                    (-1, 1), (1, 1)]
        nextNodeInDiagonal = False

        if self.pos in graph.groundNodes and nextNode in graph.groundNodes:
            for node in diagonal:
                if (self.pos[0] + node[0], self.pos[1] + node[1]) == nextNode:
                    self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (self, self, Enumerations.message_type.move, 14 * self.speed, nextNode)
                    nextNodeInDiagonal = True
            if not nextNodeInDiagonal:
                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                    (self, self, Enumerations.message_type.move, 10 * self.speed, nextNode)

        elif (self.pos in graph.groundNodes and nextNode in graph.swampNodes) or \
                (self.pos in graph.swampNodes and nextNode in graph.groundNodes):
            for node in diagonal:
                if (self.pos[0] + node[0], self.pos[1] + node[1]) == nextNode:
                    self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (self, self, Enumerations.message_type.move, 21 * self.speed, nextNode)
                    nextNodeInDiagonal = True
            if not nextNodeInDiagonal:
                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                    (self, self, Enumerations.message_type.move, 15 * self.speed, nextNode)

        elif self.pos in graph.swampNodes and nextNode in graph.swampNodes:
            for node in diagonal:
                if (self.pos[0] + node[0], self.pos[1] + node[1]) == nextNode:
                    self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (self, self, Enumerations.message_type.move, 28 * self.speed, nextNode)
                    nextNodeInDiagonal = True
            if not nextNodeInDiagonal:
                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                    (self, self, Enumerations.message_type.move, 20 * self.speed, nextNode)

        self.stateMachine.changeState(States.States.idle)
