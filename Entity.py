import States
import Enumerations
import Algorithms
import Objects
import random


class Entity:
    def __init__(self, occupation, pos, entityManager, ID):
        self.occupation = occupation
        self.pos = pos
        self.entityManager = entityManager
        self.stateMachine = None
        self.ID = ID
        self.variables = {}
        self.route = []
        self.speed = 0.0001  # lower value is faster, 1 is normal speed
        self.destinationDistance = 0
        self.destination = []  # [0] is (x, y), [1] is location_type
        self.isWorking = False

    def __lt__(self, other):
        if self.occupation == "discoverer" and len(self.variables["nextFogNode"]) is not None:  # goal is variables["newFogNode"]
            # if Algorithms.heuristic(self.variables["nextFogNode"], self.pos) < \
            #         Algorithms.heuristic(other.variables["nextFogNode"], other.pos):
            return True
        else:
            if len(other.destination) > 0 and len(self.destination) > 0:
                if Algorithms.heuristic(self.destination[0], self.pos) < \
                        Algorithms.heuristic(other.destination[0], other.pos):
                    return True
        return False

    def __le__(self, other):
        if self.occupation == "discoverer":  # goal is variables["newFogNode"]
            if Algorithms.heuristic(self.variables["nextFogNode"], self.pos) <= \
                    Algorithms.heuristic(other.variables["nextFogNode"], other.pos):
                return True
        else:
            if Algorithms.heuristic(self.destination[0], self.pos) <= \
                    Algorithms.heuristic(other.destination[0], other.pos):
                return True
        return False

    def update(self):
        # upgrade to discoverer if needed
        if self.occupation == "worker" and self.stateMachine.currentState is States.States.wandering and \
                self.entityManager.worldManager.needDiscoverers and self.variables["item"] is None:

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
            if self.variables["item"] is not None:
                self.entityManager.worldManager.gatheredTreesAvailable -= 1
            self.variables.popitem()
            self.variables["nextFogNode"] = None
            if len(self.entityManager.discoverers) >= 20:
                self.entityManager.worldManager.needDiscoverers = False

            # release tree
            while len(self.destination) > 0:
                self.destination.pop(0)
            self.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, self)
            self.isWorking = False

            self.stateMachine.changeState(States.States.discover)

        elif telegram.msg == Enumerations.message_type.move:
            self.pos = telegram.extraInfo

            if self.occupation == "discoverer":
                self.stateMachine.changeState(States.States.discover)

            elif self.occupation == "worker":
                if not self.isWorking:
                    self.stateMachine.changeState(States.States.wandering)
                elif self.isWorking:
                    if len(self.destination) <= 0:
                        print("no destination :(")
                        print("no destination :(")
                    elif self.pos == self.destination[0] and self.destination[1] == Enumerations.location_type.tree:
                        if self.pos not in self.entityManager.worldManager.trees:
                            print("Tree is not here anymore D: Where did it get removed??")
                        # for all workers who have this pos as destination, remove their destination, set to wandering
                        for worker in self.entityManager.workers:
                            if len(worker.destination) > 0 and worker is not self and worker.destination[0] == self.pos:
                                # for all pathsToFind[3] that is this pos
                                for pathToFind in self.entityManager.worldManager.pathsToFind:
                                    if pathToFind[1][3] == self.pos:
                                        # if this path search is ongoing
                                        if self.entityManager.worldManager.pathsToFind[0] is pathToFind:
                                            self.entityManager.worldManager.priorityQ.clear()
                                        self.entityManager.worldManager.pathsToFind.remove(pathToFind)

                                while len(worker.destination) > 0:
                                    worker.destination.pop(0)
                                worker.stateMachine.changeState(States.States.wandering)

                        self.stateMachine.changeState(States.States.chopTree)

                    elif self.pos == self.destination[0] and self.destination[1] == Enumerations.location_type.kiln:
                        # send msg to kilnManager at this pos, recieveItem
                        for kilnManager in self.entityManager.kilnManagers:
                            if kilnManager.pos == self.pos:
                                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                                    (kilnManager, self, Enumerations.message_type.recieveMaterial, 0, \
                                     self.variables["item"])
                        while len(self.destination) > 0:
                            self.destination.pop(0)
                        # look for tree
                        # for tree in self.entityManager.worldManager.trees:
                        #     # if tree with no owner found, add to distance if it's empty, else check distance
                        #     if self.entityManager.worldManager.trees[tree].owner is None:
                        #         if len(self.destination) <= 0:
                        #             self.destination.append(tree)
                        #             self.destination.append(Enumerations.location_type.tree)
                        #         else:
                        #             # check if its distance is shorter than current destinationDistance
                        #             distance = Algorithms.heuristic(tree, self.pos)
                        #             otherDistance = Algorithms.heuristic(self.destination[0], self.pos)
                        #             # if shorter for self, change worker of tree to self, changeState(ChopTree)
                        #             if distance < otherDistance:
                        #                 self.destination[0] = tree
                        if len(self.destination) <= 0:
                            # if no tree found
                            self.stateMachine.changeState(States.States.wandering)
                        else:
                            self.stateMachine.changeState(States.States.chopTree)

                    elif self.pos == self.destination[0] and self.destination[1] == Enumerations.location_type.builder:
                        builderFound = False
                        for builder in self.entityManager.builders:  # find the builder for this pos
                            if builder.pos == self.pos:  # safe to hand over its tree
                                builderFound = True
                                self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                                    (builder, self, Enumerations.message_type.recieveMaterial, 0, \
                                     self.variables["item"])
                                while len(self.destination) > 0:
                                    self.destination.pop(0)
                                self.stateMachine.changeState(States.States.wandering)
                                break

                        if not builderFound:  # builder is not here anymore
                            while len(self.destination) > 0:
                                self.destination.pop(0)
                            self.stateMachine.changeState(States.States.idle)

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
                if len(self.destination) > 0 and \
                        self.pos == self.destination[0] and self.destination[1] == Enumerations.location_type.kiln:
                    # if building is here, set its owner
                    if self.pos in self.entityManager.worldManager.buildings:

                        # if building doesn't belong to someone else
                        if self.entityManager.worldManager.buildings[self.pos].owner is None or \
                                self.entityManager.worldManager.buildings[self.pos].owner is self:
                            self.entityManager.worldManager.buildings[self.pos].owner = self
                            self.stateMachine.changeState(States.States.manageKiln)

                        else:  # if it does belong to someone else
                            while len(self.destination) > 0:
                                self.destination.pop(0)

                            self.isWorking = False
                            self.stateMachine.changeState(States.States.idle)

                    else:  # if building is not here, just manageKiln
                        self.stateMachine.changeState(States.States.manageKiln)

                elif self.isWorking:
                    self.stateMachine.changeState(States.States.moveToDestination)
                else:
                    self.stateMachine.changeState(States.States.idle)

        # elif telegram.msg == Enumerations.message_type.treeAppeared:
        #     # handle message if this entity wants a tree to chop
        #     if not self.isWorking and self.variables["item"] is None:
        #         # check if tree has owner
        #         if self.entityManager.worldManager.trees[telegram.extraInfo].owner is not None:
        #             # if occupied, check if distance is shorter for self
        #             distance = Algorithms.heuristic(telegram.extraInfo, self.pos)
        #             otherDistance = Algorithms.heuristic \
        #                 (telegram.extraInfo, self.entityManager.worldManager.trees[telegram.extraInfo].owner.pos)
        #             # if shorter for self, change worker of tree to self, changeState(ChopTree)
        #             # this is where pathsToFind is neglected D:
        #             # TODO: fix pathsToFind to match current state
        #             if distance < otherDistance:
        #                 # make previous owner change state to wandering
        #                 self.entityManager.worldManager.trees[telegram.extraInfo].owner.destination.pop(0)
        #                 self.entityManager.worldManager.trees[telegram.extraInfo].owner.destination.pop(0)
        #                 self.entityManager.worldManager.trees[telegram.extraInfo].owner.route.clear()
        #                 self.entityManager.worldManager.trees[telegram.extraInfo].owner. \
        #                     stateMachine.changeState(States.States.wandering)
        #
        #                 self.entityManager.worldManager.trees[telegram.extraInfo].owner = self
        #                 while len(self.destination) > 0:
        #                     self.destination.pop(0)
        #                 self.destination.append(telegram.extraInfo)
        #                 self.destination.append(Enumerations.location_type.tree)
        #                 self.stateMachine.changeState(States.States.chopTree)
        #
        #         # if not occupied, change worker tree to self, changeState(ChopTree)
        #         else:
        #             self.entityManager.worldManager.trees[telegram.extraInfo].owner = self
        #             # change destination to tree
        #             while len(self.destination) > 0:
        #                 self.destination.pop(0)
        #             self.destination.append(telegram.extraInfo)
        #             self.destination.append(Enumerations.location_type.tree)
        #             self.stateMachine.changeState(States.States.chopTree)

        elif telegram.msg == Enumerations.message_type.treeIsChopped:
            if self.occupation == "discoverer":
                # reset owner etc
                telegram.extraInfo.owner = None
            elif self.occupation == "kilnManager":
                telegram.extraInfo.owner = None
            else:
                # self.entityManager.worldManager.gatheredTreesAvailable += 1
                if self.pos not in self.entityManager.worldManager.trees:
                    print("tree is not here")  # destination is set to kilnManager while chopping tree
                    self.variables["item"] = None  # apparently it upgraded to discoverer while chopping tree
                else:
                    self.variables["item"] = self.entityManager.worldManager.trees[self.pos]
                    self.entityManager.worldManager.trees.pop(self.pos, telegram.extraInfo)
                # add new tree
                self.entityManager.worldManager.graph.freeGroundNodes.append(self.pos)
                newTree = self.entityManager.worldManager.addNewTree()
                if newTree.pos in self.entityManager.worldManager.graph.freeGroundNodes:
                    self.entityManager.worldManager.graph.freeGroundNodes.remove(newTree.pos)

                # if newTree.pos not in self.entityManager.worldManager.graph.fogNodes:
                #     for entity in self.entityManager.workers:
                #         if entity not in self.entityManager.isUpgrading:
                #             self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                #                 (entity, self, Enumerations.message_type.treeAppeared, 0, newTree.pos)

                # not sure why I have this as an entity field but it's reset here every time so whatever
                self.destinationDistance = 1000000
                while len(self.destination) > 0:
                    self.destination.pop(0)
                self.destination.append(self.pos)
                self.destination.append(None)

                # find builder who needs trees
                if self.entityManager.worldManager.needKiln:
                    for builder in self.entityManager.builders:
                        # if builder needs trees, set destination
                        if not builder.isWorking and len(builder.variables["items"]) < 1:
                            # set destination to this builder, break
                            self.destination[0] = builder.pos
                            self.destination[1] = Enumerations.location_type.builder
                            break

                            # decide spot to build for this builder
                            # NOTE: only works if worldManager only has one builder
                            # while len(builder.destination) > 0:
                            #     builder.destination.pop(0)
                            # for spot in self.entityManager.worldManager.buildingSpots:
                            #     if spot not in self.entityManager.worldManager.buildings and \
                            #             spot not in self.entityManager.worldManager.graph.fogNodes:
                            #         builder.destination.append(spot)
                            #         builder.destination.append(Enumerations.location_type.kiln)
                            #     # if kiln not found, do nothing
                            # if len(builder.destination) > 0:
                            #     builder.stateMachine.changeState(States.States.build)
                                # for kilnManager in self.entityManager.kilnManagers:  # do this in buildingIsDone
                                #     if not kilnManager.isWorking:
                                #         kilnManager.destination.append(builder.destination[0])
                                #         kilnManager.destination.append(Enumerations.location_type.kiln)
                                #         kilnManager.stateMachine.changeState(States.States.manageKiln)
                                #         break

                else:  # find nearest kilnManager
                    for kilnManager in self.entityManager.kilnManagers:
                        newDistance = Algorithms.heuristic(kilnManager.pos, self.pos)
                        if newDistance < self.destinationDistance and \
                                kilnManager.pos in self.entityManager.worldManager.buildings:
                            self.destinationDistance = newDistance
                            self.destination[0] = kilnManager.pos
                            self.destination[1] = Enumerations.location_type.kiln

                # start carrying tree if destination is found
                if self.destination[1] is not None:
                    self.stateMachine.changeState(States.States.carryTree)
                else:
                    self.destination.pop(0)
                    self.destination.pop(0)
                    self.stateMachine.changeState(States.States.idle)

        elif telegram.msg == Enumerations.message_type.isUpgradedBuilder:
            self.occupation = "builder"
            self.entityManager.builders.append(self)
            self.entityManager.isUpgrading.remove(self)
            self.entityManager.workers.remove(self)
            self.variables.popitem()
            self.variables["isBuilding"] = False
            self.variables["items"] = []  # list of tree objects

            self.entityManager.worldManager.needBuilders = False
            self.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, self)
            self.route.clear()
            self.isWorking = False
            while len(self.destination) > 0:
                self.destination.pop(0)

            self.stateMachine.changeState(States.States.idle)

        elif telegram.msg == Enumerations.message_type.buildingIsDone:
            self.entityManager.worldManager.buildings[self.pos] = Objects.Kiln(self.pos)
            self.entityManager.worldManager.graph.freeGroundNodes.remove(self.pos)

            self.isWorking = False
            self.variables["isBuilding"] = False
            for treesRequired in range(1):
                # remove first inserted tree from items
                self.variables["items"].pop(0)

            # set needKiln to False if amount of buildings has reached max (4)
            # if len(self.entityManager.worldManager.buildings) >= 4:
            #     self.entityManager.worldManager.needKiln = False

            # set kilnManager for this pos to owner
            for kilnManager in self.entityManager.kilnManagers:
                if kilnManager.pos == self.pos:
                    self.entityManager.worldManager.buildings[self.pos].owner = kilnManager
                    if not kilnManager.isWorking:
                        while len(kilnManager.destination) > 0:
                            kilnManager.destination.pop(0)
                        kilnManager.destination.append(self.pos)
                        kilnManager.destination.append(Enumerations.location_type.kiln)
                        kilnManager.stateMachine.changeState(States.States.manageKiln)
                    break
            # if not at this pos, for loop through kilnManagers
            if self.entityManager.worldManager.buildings[self.pos].owner is None:
                for kilnManager in self.entityManager.kilnManagers:
                    if not kilnManager.isWorking or len(kilnManager.destination) > 0:
                        self.entityManager.worldManager.buildings[self.pos].owner = kilnManager
                        while len(kilnManager.destination) > 0:
                            kilnManager.destination.pop(0)
                        kilnManager.destination.append(self.pos)
                        kilnManager.destination.append(Enumerations.location_type.kiln)
                        kilnManager.stateMachine.changeState(States.States.manageKiln)
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
            self.isWorking = False

            # for when max amount of kilnManagers is reached.
            # Not doing much if enabled anyway since builder is the one who decides if kilnManager is needed.
            # if len(self.entityManager.kilnManagers) < 4:
            #     self.entityManager.worldManager.needKilnManager = True
            # else:
            #     self.entityManager.worldManager.needKilnManager = False

            # this will probably cause the bug I struggled with yesterday, except it's not a worker.
            # I remember seeing similar behaviour on a kilnManager sometimes before and this is most likely why
            # self.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, self)

            self.route.clear()  # NOTE: mysterious reset, might not be safe
            while len(self.destination) > 0:
                self.destination.pop(0)

            # check if any empty buildings, changeState.manageKiln
            for building in self.entityManager.worldManager.buildings:
                if self.entityManager.worldManager.buildings[building].owner is None:
                    self.entityManager.worldManager.buildings[building].owner = self
                    self.destination.append(building)
                    self.destination.append(Enumerations.location_type.kiln)
                    self.stateMachine.changeState(States.States.manageKiln)
                    break

            if len(self.destination) <= 0:  # if no building found, wait for builder to call it
                self.stateMachine.changeState(States.States.idle)

        elif telegram.msg == Enumerations.message_type.charcoalIsDone:
            self.entityManager.worldManager.charcoal += 1
            self.variables["items"].pop(0)

            if self.entityManager.worldManager.charcoal >= 200:
                print("200 charcoal has been made! :D Betyg 3 är nått!")
            else:
                for worker in self.entityManager.workers:
                    if worker.variables["item"] is not None and \
                            worker.stateMachine.currentState is not States.States.carryTree and \
                            worker.stateMachine.currentState is not States.States.chopTree and \
                            len(worker.destination) <= 0:
                        self.entityManager.worldManager.messageDispatcher.dispatchMessage \
                            (worker, self, Enumerations.message_type.giveMeTrees, 0, None)

            self.variables["isMakingCharcoal"] = False

        elif telegram.msg == Enumerations.message_type.recieveMaterial:
            self.variables["items"].append(telegram.extraInfo)
            # self.entityManager.worldManager.trees.pop\
            #     (telegram.extraInfo.pos, telegram.extraInfo)
            telegram.sender.variables["item"] = None
            if self.occupation == "builder":
                # if builder has enough trees, start building
                if len(self.variables["items"]) >= 1:
                    self.entityManager.worldManager.needKilnManager = True

                    # set destination to free buildingSpot
                    while len(self.destination) > 0:
                        self.destination.pop(0)
                    for spot in self.entityManager.worldManager.buildingSpots:
                        if spot not in self.entityManager.worldManager.buildings and \
                                spot not in self.entityManager.worldManager.graph.fogNodes:
                            self.destination.append(spot)
                            self.destination.append(Enumerations.location_type.kiln)
                            break

                    if len(self.destination) > 0:  # if kiln found, start building
                        self.entityManager.worldManager.needKiln = False
                        self.stateMachine.changeState(States.States.build)
                    else:  # if destination not found, set to idle
                        self.stateMachine.changeState(States.States.idle)

            elif self.occupation == "kilnManager":  # make more kilns if this kilnManager has enough trees
                if (len(self.variables["items"]) > (1 + 1) and self.variables["isMakingCharcoal"]) or \
                        (len(self.variables["items"]) > 1 and not self.variables["isMakingCharcoal"]):
                    self.entityManager.worldManager.needKiln = True

        elif telegram.msg == Enumerations.message_type.giveMeTrees:
            while len(self.destination) > 0:
                self.destination.pop(0)
            self.destination.append(telegram.sender.pos)
            self.destination.append(Enumerations.location_type.kiln)
            self.stateMachine.changeState(States.States.carryTree)

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
