import random
import Objects
import MessageSystem
import States
import Enumerations
import heapq
import Algorithms


class WorldManager:
    def __init__(self, entityManager, graph):
        self.entityManager = entityManager
        self.graph = graph
        self.trees = {}  # {(x, y) : Tree object}
        self.buildings = {}  # {(x, y) : Building object}
        self.messageDispatcher = MessageSystem.MessageDispatcher()
        self.states = States.States()
        self.needDiscoverers = True
        self.needBuilders = True
        self.needKilnManager = False
        self.gatheredTreesAvailable = 0
        self.needKiln = True
        self.AStarHasOccurred = False
        self.charcoal = 0
        self.buildingSpots = [(72, 90), (23, 90), (72, 37), (26, 11)]
        # path finding
        self.pathsToFind = []
        self.discoverPathsToFind = []
        self.craftsmanPathsToFind = []
        self.iterationsPerUpdate = 15
        self.iterationsSoFar = 0
        self.pathsFoundForWorkers = 0

        self.costSoFar = {}
        self.AStarCostSoFar = {}
        self.discoverCostSoFar = {}
        self.discoverAStarCostSoFar = {}
        self.craftsmanCostSoFar = {}
        self.craftsmanAStarCostSoFar = {}

        self.priorityQ = []
        self.AStarPriorityQ = []
        self.discoverPriorityQ = []
        self.discoverAStarPriorityQ = []
        self.craftsmanPriorityQ = []
        self.craftsmanAStarPriorityQ = []

        self.path = {}
        self.AStarPath = {}
        self.discoverPath = {}
        self.discoverAStarPath = {}
        self.craftsmanPath = {}
        self.craftsmanAStarPath = {}
        # self.pathFound = False

    def update(self):
        # upgrading to builder and kilnManager
        if self.needBuilders:
            for entity in self.entityManager.workers:
                if not entity.isWorking and entity not in self.entityManager.isUpgrading:
                    entity.stateMachine.changeState(self.states.upgradingToBuilder)
                    self.needBuilders = False
                    break
        if self.needKilnManager:
            for entity in self.entityManager.workers:
                if not entity.isWorking and entity not in self.entityManager.isUpgrading:
                    entity.stateMachine.changeState(self.states.upgradingToKilnManager)
                    self.needKilnManager = False
                    break
        if self.needKiln:
            for builder in self.entityManager.builders:
                if not builder.isWorking and len(builder.variables["items"]) >= 1:
                    # look for free buildingSpot not in fogNode
                    while len(builder.destination) > 0:
                        builder.destination.pop(0)
                    for spot in self.buildingSpots:
                        if spot not in self.buildings and spot not in self.graph.fogNodes:
                            builder.destination.append(spot)
                            builder.destination.append(Enumerations.location_type.kiln)
                            break

                    if len(builder.destination) > 0:  # if kiln found, start building
                        self.needKiln = False
                        builder.stateMachine.changeState(self.states.build)
                    else:  # if destination not found, set to idle
                        builder.stateMachine.changeState(self.states.idle)

        # make all free trees request to be chopped
        for tree in self.trees:
            if self.trees[tree].owner is None and tree not in self.graph.fogNodes:

                # if heuristic <= 72, break. A close worker has been found.
                shortestDistance = 100000000000000000000
                closestWorker = None
                for worker in self.entityManager.workers:
                    newDistance = Algorithms.heuristic(tree, worker.pos)
                    if not worker.isWorking and newDistance <= 100 and worker not in self.entityManager.isUpgrading:
                        while len(worker.destination) > 0:
                            worker.destination.pop(0)
                        worker.destination.append(tree)
                        worker.destination.append(Enumerations.location_type.tree)
                        self.trees[tree].owner = worker
                        worker.stateMachine.changeState(self.states.chopTree)
                        break
                    elif not worker.isWorking and newDistance < shortestDistance:
                        shortestDistance = newDistance
                        closestWorker = worker
                # if closest found worker is further away than 72, set it to owner
                if closestWorker is not None:
                    while len(closestWorker.destination) > 0:
                        closestWorker.destination.pop(0)
                    closestWorker.destination.append(tree)
                    closestWorker.destination.append(Enumerations.location_type.tree)
                    self.trees[tree].owner = closestWorker
                    closestWorker.stateMachine.changeState(self.states.chopTree)

        self.AStarHasOccurred = False
        self.entityManager.update()

    def addNewTree(self):
        treeIndex = random.randrange(0, len(self.graph.treeNodes))
        foundFreeNode = False
        while not foundFreeNode:
            foundFreeNode = True
            for tree in self.trees:
                if self.graph.treeNodes[treeIndex] == self.trees[tree].pos:
                    treeIndex = random.randrange(0, len(self.graph.treeNodes))
                    foundFreeNode = False
                    break

        tree = Objects.Tree(self.graph.treeNodes[treeIndex])
        self.trees[self.graph.treeNodes[treeIndex]] = tree

        return tree

    def handleMessage(self, telegram):
        if telegram.msg == Enumerations.message_type.stopUpgrading:
            for message in self.messageDispatcher.priorityQ:
                # find message for upgrading sender entity
                if message[1].sender is telegram.sender and \
                        message[1].msg == Enumerations.message_type.isUpgradedDiscoverer:
                    self.messageDispatcher.priorityQ.remove(message)

    def removeAllMessagesOf(self, messageType, entity):
        for message in self.messageDispatcher.priorityQ:
            if message[1].reciever is entity and message[1].msg == messageType:
                self.messageDispatcher.toBeRemoved.append((messageType, entity))
                # self.messageDispatcher.priorityQ.remove(message)
                # kom på att det inte går att ta bort ett meddelande mitt i en heap... what do I do then Dx??
                # jag kan lägga meddelandet i en lista som messageDispatcher jämför med när meddelandet dyker upp i
                # heapen o:
                # om meddelandet är i listan så ska det inte skickas, och det poppas bort ur heapen
                # det tas även bort från listan med remove

    def doPathFinding(self):
        if len(self.craftsmanPathsToFind) > 0:
            if len(self.craftsmanPriorityQ) == 0:  # new entity
                self.craftsmanAStarPriorityQ.clear()
                heapq.heappush(self.craftsmanAStarPriorityQ, (0, tuple(self.craftsmanPathsToFind[0][1][2])))
                self.craftsmanAStarPath.clear()
                self.craftsmanAStarCostSoFar.clear()
                self.craftsmanAStarPath[tuple(self.craftsmanPathsToFind[0][1][2])] = None
                self.craftsmanAStarCostSoFar[tuple(self.craftsmanPathsToFind[0][1][2])] = 0
            else:  # set A* variables to progress values
                if self.craftsmanPathsToFind[0][1][2] not in self.craftsmanPath:
                    print("why start not in path..? D:")
                self.craftsmanAStarPriorityQ = self.craftsmanPriorityQ
                self.craftsmanAStarPath = self.craftsmanPath
                self.craftsmanAStarCostSoFar = self.craftsmanCostSoFar

            while self.iterationsSoFar <= self.iterationsPerUpdate:
                if len(self.craftsmanAStarPriorityQ) == 0:
                    self.craftsmanPathsToFind[0][1][0].route = [(0, 0)]
                    self.craftsmanAStarPriorityQ.clear()
                    self.craftsmanAStarPath.clear()
                    self.craftsmanAStarCostSoFar.clear()
                    heapq.heappop(self.craftsmanPathsToFind)[1]
                    if len(self.craftsmanPathsToFind) > 0:
                        # heapq.heapify(self.pathsToFind)
                        # if self.pathsToFind[0][1][0].occupation == "discoverer":
                        #     for path in self.pathsToFind:
                        #         if path[1][0].occupation != "discoverer":
                        #             while self.pathsToFind[0][1][0].occupation == "discoverer":
                        #                 oldPath = heapq.heappop(self.pathsToFind)
                        #                 heapq.heappush(self.pathsToFind, oldPath)
                        #                 # self.pathsToFind.append(oldPath)
                        #             break

                        self.doPathFinding()
                    break

                self.iterationsSoFar += 1
                currentNode = heapq.heappop(self.craftsmanAStarPriorityQ)[1]

                if currentNode == tuple(self.craftsmanPathsToFind[0][1][3]):
                    if self.craftsmanPathsToFind[0][1][2] not in self.craftsmanAStarPath:
                        print("why start not in path..? D:")
                    if self.craftsmanAStarPath[self.craftsmanPathsToFind[0][1][2]] is not None:
                        print("will get an error :((")
                    self.craftsmanPathsToFind[0][1][0].route = Algorithms.getRoute \
                        (self.craftsmanPathsToFind[0][1][2], self.craftsmanPathsToFind[0][1][3], self.craftsmanAStarPath)
                    self.craftsmanAStarPriorityQ.clear()
                    self.craftsmanAStarPath.clear()
                    self.craftsmanAStarCostSoFar.clear()
                    self.craftsmanPriorityQ.clear()
                    self.craftsmanPath.clear()
                    self.craftsmanCostSoFar.clear()
                    heapq.heappop(self.craftsmanPathsToFind)[1]
                    if len(self.craftsmanPathsToFind) > 0:
                        # heapq.heapify(self.pathsToFind)
                        # if self.pathsToFind[0][1][0].occupation == "discoverer":
                        #     for path in self.pathsToFind:
                        #         if path[1][0].occupation != "discoverer":
                        #             while self.pathsToFind[0][1][0].occupation == "discoverer":
                        #                 oldPath = heapq.heappop(self.pathsToFind)
                        #                 heapq.heappush(self.pathsToFind, oldPath)
                        #                 # self.pathsToFind.append(oldPath)
                        #             break

                        self.doPathFinding()
                    break

                for neighbour in self.craftsmanPathsToFind[0][1][1].neighboursExceptFog(currentNode):
                    if neighbour not in self.craftsmanPathsToFind[0][1][1].fogNodes:
                        newCost = self.craftsmanAStarCostSoFar[currentNode] + \
                                  Algorithms.tileDependentHeuristic \
                                      (self.craftsmanPathsToFind[0][1][1], neighbour, currentNode)
                        if (tuple(neighbour) not in self.craftsmanAStarCostSoFar) or \
                                (newCost < self.craftsmanAStarCostSoFar[tuple(neighbour)]):
                            self.craftsmanAStarCostSoFar[tuple(neighbour)] = newCost
                            priority = newCost + Algorithms.heuristic(self.craftsmanPathsToFind[0][1][3], neighbour)
                            self.craftsmanAStarPath[tuple(neighbour)] = currentNode
                            heapq.heappush(self.craftsmanAStarPriorityQ, (priority, tuple(neighbour)))
                    else:  # if neighbour is in a fogNode, plz don't choose this node I beg you :((
                        newCost = self.craftsmanAStarCostSoFar[currentNode] + 10000000000000000000000000000000000
                        if (tuple(neighbour) not in self.craftsmanAStarCostSoFar) or \
                                (newCost < self.craftsmanAStarCostSoFar[tuple(neighbour)]):
                            self.craftsmanAStarCostSoFar[tuple(neighbour)] = newCost
                            priority = newCost + Algorithms.heuristic(self.craftsmanPathsToFind[0][1][3], neighbour)
                            self.craftsmanAStarPath[tuple(neighbour)] = currentNode
                            heapq.heappush(self.craftsmanAStarPriorityQ, (priority, tuple(neighbour)))

            self.iterationsSoFar = 0
            self.craftsmanPriorityQ = self.craftsmanAStarPriorityQ
            self.craftsmanPath = self.craftsmanAStarPath
            self.craftsmanCostSoFar = self.craftsmanAStarCostSoFar

        elif len(self.pathsToFind) > 0 and self.pathsFoundForWorkers <= 5:  # 0:entity, 1:graph, 2:start, 3:goal

            # if self.pathsToFind[0][1][0].occupation == "discoverer":
            #     if len(self.priorityQ) == 0:  # new entity
            #         self.AStarPriorityQ.clear()
            #         heapq.heappush(self.AStarPriorityQ, (0, tuple(self.pathsToFind[0][1][2])))
            #         self.AStarPath[tuple(self.pathsToFind[0][1][2])] = None
            #         self.AStarCostSoFar[tuple(self.pathsToFind[0][1][2])] = 0
            #     else:  # set A* variables to progress values
            #         self.AStarPriorityQ = self.priorityQ
            #         self.AStarPath = self.path
            #         self.AStarCostSoFar = self.costSoFar
            #
            #     while self.iterationsSoFar <= self.iterationsPerUpdate:
            #         if len(self.AStarPriorityQ) == 0:  # return an invalid tuple if no path found
            #             self.pathsToFind[0][1][0].route = [(0, 0)]
            #             self.AStarPriorityQ.clear()
            #             self.AStarPath.clear()
            #             self.AStarCostSoFar.clear()
            #             heapq.heappop(self.pathsToFind)[1]
            #             if len(self.pathsToFind) > 0:
            #                 # if a non discoverer has a shorter path than discoverer in front, set it to front, break
            #                 # set a non discoverer to the front if there is one
            #                 heapq.heapify(self.pathsToFind)
            #                 if self.pathsToFind[0][1][0].occupation == "discoverer":
            #                     for path in self.pathsToFind:
            #                         if path[1][0].occupation != "discoverer":
            #                             while self.pathsToFind[0][1][0].occupation == "discoverer":
            #                                 oldPath = heapq.heappop(self.pathsToFind)
            #                                 heapq.heappush(self.pathsToFind, oldPath)
            #                                 # self.pathsToFind.append(oldPath)
            #                             break
            #
            #                 # for path in paths, check if path
            #                 self.doPathFinding()
            #             break
            #
            #         currentNode = heapq.heappop(self.AStarPriorityQ)[1]
            #
            #         if currentNode == tuple(self.pathsToFind[0][1][3]):
            #             if self.AStarPath[self.pathsToFind[0][1][2]] is not None:
            #                 print("will get an error :((")
            #             self.pathsToFind[0][1][0].route = Algorithms.getRoute \
            #                 (self.pathsToFind[0][1][2], self.pathsToFind[0][1][3], self.AStarPath)
            #             self.AStarPriorityQ.clear()
            #             self.AStarPath.clear()
            #             self.AStarCostSoFar.clear()
            #             self.priorityQ.clear()
            #             self.path.clear()
            #             self.costSoFar.clear()
            #             heapq.heappop(self.pathsToFind)[1]
            #             if len(self.pathsToFind) > 0:
            #                 heapq.heapify(self.pathsToFind)
            #                 if self.pathsToFind[0][1][0].occupation == "discoverer":
            #                     for path in self.pathsToFind:
            #                         if path[1][0].occupation != "discoverer":
            #                             while self.pathsToFind[0][1][0].occupation == "discoverer":
            #                                 oldPath = heapq.heappop(self.pathsToFind)
            #                                 heapq.heappush(self.pathsToFind, oldPath)
            #                                 # self.pathsToFind.append(oldPath)
            #                             break
            #
            #                 self.doPathFinding()
            #             break
            #
            #         for neighbour in self.pathsToFind[0][1][1].neighbours(currentNode):
            #             newCost = self.AStarCostSoFar[currentNode] + \
            #                       Algorithms.tileDependentHeuristic(self.pathsToFind[0][1][1], neighbour, currentNode)
            #             if (tuple(neighbour) not in self.AStarCostSoFar) or \
            #                     (newCost < self.AStarCostSoFar[tuple(neighbour)]):
            #                 self.AStarCostSoFar[tuple(neighbour)] = newCost
            #                 priority = newCost + Algorithms.heuristic(self.pathsToFind[0][1][3], neighbour)
            #                 self.AStarPath[tuple(neighbour)] = currentNode
            #                 heapq.heappush(self.AStarPriorityQ, (priority, tuple(neighbour)))
            #
            #         self.iterationsSoFar += 1
            #
            #     self.iterationsSoFar = 0
            #     self.priorityQ = self.AStarPriorityQ
            #     self.path = self.AStarPath
            #     self.costSoFar = self.AStarCostSoFar

            # else:  # if entity is not discoverer, avoid fog
            if len(self.priorityQ) == 0:  # new entity
                self.AStarPriorityQ.clear()
                heapq.heappush(self.AStarPriorityQ, (0, tuple(self.pathsToFind[0][1][2])))
                self.AStarPath.clear()
                self.AStarCostSoFar.clear()
                self.AStarPath[tuple(self.pathsToFind[0][1][2])] = None
                self.AStarCostSoFar[tuple(self.pathsToFind[0][1][2])] = 0
            else:  # set A* variables to progress values
                if self.pathsToFind[0][1][2] not in self.path:
                    print("why start not in path..? D:")
                self.AStarPriorityQ = self.priorityQ
                self.AStarPath = self.path
                self.AStarCostSoFar = self.costSoFar

            while self.iterationsSoFar <= self.iterationsPerUpdate:
                if len(self.AStarPriorityQ) == 0:
                    self.pathsToFind[0][1][0].route = [(0, 0)]
                    self.AStarPriorityQ.clear()
                    self.AStarPath.clear()
                    self.AStarCostSoFar.clear()
                    heapq.heappop(self.pathsToFind)[1]
                    if self.pathsFoundForWorkers > 5:
                        self.pathsFoundForWorkers = 0
                    else:
                        self.pathsFoundForWorkers += 1
                    if len(self.pathsToFind) > 0:
                        # heapq.heapify(self.pathsToFind)
                        # if self.pathsToFind[0][1][0].occupation == "discoverer":
                        #     for path in self.pathsToFind:
                        #         if path[1][0].occupation != "discoverer":
                        #             while self.pathsToFind[0][1][0].occupation == "discoverer":
                        #                 oldPath = heapq.heappop(self.pathsToFind)
                        #                 heapq.heappush(self.pathsToFind, oldPath)
                        #                 # self.pathsToFind.append(oldPath)
                        #             break

                        self.doPathFinding()
                    break

                self.iterationsSoFar += 1
                currentNode = heapq.heappop(self.AStarPriorityQ)[1]

                if currentNode == tuple(self.pathsToFind[0][1][3]):
                    if self.pathsToFind[0][1][2] not in self.AStarPath:
                        print("why start not in path..? D:")
                    if self.AStarPath[self.pathsToFind[0][1][2]] is not None:
                        print("will get an error :((")
                    self.pathsToFind[0][1][0].route = Algorithms.getRoute \
                        (self.pathsToFind[0][1][2], self.pathsToFind[0][1][3], self.AStarPath)
                    self.AStarPriorityQ.clear()
                    self.AStarPath.clear()
                    self.AStarCostSoFar.clear()
                    self.priorityQ.clear()
                    self.path.clear()
                    self.costSoFar.clear()
                    heapq.heappop(self.pathsToFind)[1]
                    if self.pathsFoundForWorkers > 5:
                        self.pathsFoundForWorkers = 0
                    else:
                        self.pathsFoundForWorkers += 1
                    if len(self.pathsToFind) > 0:
                        # heapq.heapify(self.pathsToFind)
                        # if self.pathsToFind[0][1][0].occupation == "discoverer":
                        #     for path in self.pathsToFind:
                        #         if path[1][0].occupation != "discoverer":
                        #             while self.pathsToFind[0][1][0].occupation == "discoverer":
                        #                 oldPath = heapq.heappop(self.pathsToFind)
                        #                 heapq.heappush(self.pathsToFind, oldPath)
                        #                 # self.pathsToFind.append(oldPath)
                        #             break

                        self.doPathFinding()
                    break

                for neighbour in self.pathsToFind[0][1][1].neighboursExceptFog(currentNode):
                    if neighbour not in self.pathsToFind[0][1][1].fogNodes:
                        newCost = self.AStarCostSoFar[currentNode] + \
                                  Algorithms.tileDependentHeuristic \
                                      (self.pathsToFind[0][1][1], neighbour, currentNode)
                        if (tuple(neighbour) not in self.AStarCostSoFar) or \
                                (newCost < self.AStarCostSoFar[tuple(neighbour)]):
                            self.AStarCostSoFar[tuple(neighbour)] = newCost
                            priority = newCost + Algorithms.heuristic(self.pathsToFind[0][1][3], neighbour)
                            self.AStarPath[tuple(neighbour)] = currentNode
                            heapq.heappush(self.AStarPriorityQ, (priority, tuple(neighbour)))
                    else:  # if neighbour is in a fogNode, plz don't choose this node I beg you :((
                        newCost = self.AStarCostSoFar[currentNode] + 10000000000000000000000000000000000
                        if (tuple(neighbour) not in self.AStarCostSoFar) or \
                                (newCost < self.AStarCostSoFar[tuple(neighbour)]):
                            self.AStarCostSoFar[tuple(neighbour)] = newCost
                            priority = newCost + Algorithms.heuristic(self.pathsToFind[0][1][3], neighbour)
                            self.AStarPath[tuple(neighbour)] = currentNode
                            heapq.heappush(self.AStarPriorityQ, (priority, tuple(neighbour)))

            self.iterationsSoFar = 0
            self.priorityQ = self.AStarPriorityQ
            self.path = self.AStarPath
            self.costSoFar = self.AStarCostSoFar

        elif len(self.discoverPathsToFind) > 0:
            self.pathsFoundForWorkers = 0
            if len(self.discoverPriorityQ) == 0:  # new entity
                self.discoverAStarPriorityQ.clear()
                heapq.heappush(self.discoverAStarPriorityQ, (0, tuple(self.discoverPathsToFind[0][1][2])))
                self.discoverAStarPath[tuple(self.discoverPathsToFind[0][1][2])] = None
                self.discoverAStarCostSoFar[tuple(self.discoverPathsToFind[0][1][2])] = 0
            else:  # set A* variables to progress values
                self.discoverAStarPriorityQ = self.discoverPriorityQ
                self.discoverAStarPath = self.discoverPath
                self.discoverAStarCostSoFar = self.discoverCostSoFar

            while self.iterationsSoFar <= self.iterationsPerUpdate:
                if len(self.discoverAStarPriorityQ) == 0:  # return an invalid tuple if no path found
                    self.discoverPathsToFind[0][1][0].route = [(0, 0)]
                    self.discoverAStarPriorityQ.clear()
                    self.discoverAStarPath.clear()
                    self.discoverAStarCostSoFar.clear()
                    heapq.heappop(self.discoverPathsToFind)[1]
                    if len(self.discoverPathsToFind) > 0:
                        # if a non discoverer has a shorter path than discoverer in front, set it to front, break
                        # set a non discoverer to the front if there is one
                        # heapq.heapify(self.discoverPathsToFind)
                        # if self.discoverPathsToFind[0][1][0].occupation == "discoverer":
                        #     for path in self.discoverPathsToFind:
                        #         if path[1][0].occupation != "discoverer":
                        #             while self.discoverPathsToFind[0][1][0].occupation == "discoverer":
                        #                 oldPath = heapq.heappop(self.discoverPathsToFind)
                        #                 heapq.heappush(self.discoverPathsToFind, oldPath)
                        #                 # self.pathsToFind.append(oldPath)
                        #             break

                        # for path in paths, check if path
                        self.doPathFinding()
                    break

                currentNode = heapq.heappop(self.discoverAStarPriorityQ)[1]

                if currentNode == tuple(self.discoverPathsToFind[0][1][3]):
                    if self.discoverAStarPath[self.discoverPathsToFind[0][1][2]] is not None:
                        print("will get an error :((")
                    self.discoverPathsToFind[0][1][0].route = Algorithms.getRoute \
                        (self.discoverPathsToFind[0][1][2], self.discoverPathsToFind[0][1][3], self.discoverAStarPath)
                    self.discoverAStarPriorityQ.clear()
                    self.discoverAStarPath.clear()
                    self.discoverAStarCostSoFar.clear()
                    self.discoverPriorityQ.clear()
                    self.discoverPath.clear()
                    self.discoverCostSoFar.clear()
                    heapq.heappop(self.discoverPathsToFind)[1]
                    if len(self.discoverPathsToFind) > 0:
                        # heapq.heapify(self.discoverPathsToFind)
                        # if self.discoverPathsToFind[0][1][0].occupation == "discoverer":
                        #     for path in self.discoverPathsToFind:
                        #         if path[1][0].occupation != "discoverer":
                        #             while self.discoverPathsToFind[0][1][0].occupation == "discoverer":
                        #                 oldPath = heapq.heappop(self.discoverPathsToFind)
                        #                 heapq.heappush(self.discoverPathsToFind, oldPath)
                        #                 # self.pathsToFind.append(oldPath)
                        #             break

                        self.doPathFinding()
                    break

                for neighbour in self.discoverPathsToFind[0][1][1].neighbours(currentNode):
                    newCost = self.discoverAStarCostSoFar[currentNode] + \
                              Algorithms.tileDependentHeuristic\
                                  (self.discoverPathsToFind[0][1][1], neighbour, currentNode)
                    if (tuple(neighbour) not in self.discoverAStarCostSoFar) or \
                            (newCost < self.discoverAStarCostSoFar[tuple(neighbour)]):
                        self.discoverAStarCostSoFar[tuple(neighbour)] = newCost
                        priority = newCost + Algorithms.heuristic(self.discoverPathsToFind[0][1][3], neighbour)
                        self.discoverAStarPath[tuple(neighbour)] = currentNode
                        heapq.heappush(self.discoverAStarPriorityQ, (priority, tuple(neighbour)))

                self.iterationsSoFar += 1

            self.iterationsSoFar = 0
            self.discoverPriorityQ = self.discoverAStarPriorityQ
            self.discoverPath = self.discoverAStarPath
            self.discoverCostSoFar = self.discoverAStarCostSoFar
