import random
import Objects
import MessageSystem
import States
import Enumerations
import heapq
import Algorithms


class WorldManager:
    def __init__(self, entityManager, graph, variables, moveVariables):
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
        # variables and moveVariables
        self.charcoalGoal = variables["charcoalGoal"]
        self.pathIterationsPerUpdate = variables["pathIterationsPerUpdate"]
        self.buildingSpots = []
        for spot in variables["buildingSpots"]:
            self.buildingSpots.append(tuple(spot))
        self.closeDistanceTreeFromWorker = variables["closeDistanceTreeFromWorker"]
        self.maxDistanceTreeFromWorker = variables["maxDistanceTreeFromWorker"]
        self.workerPathsPerDiscoverer = variables["workerPathsPerDiscoverer"]
        self.maxDiscovererAmount = variables["maxDiscovererAmount"]
        self.minimumBuildings = variables["minimumBuildings"]

        self.moveVariables = moveVariables

        # path finding
        self.pathsToFind = []
        self.discoverPathsToFind = []
        self.craftsmanPathsToFind = []
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
                if not builder.isWorking and len(builder.variables["items"]) >= \
                        builder.entityVariables["treesPerBuilding"]:
                    # set destination to freeGroundNode
                    while len(builder.destination) > 0:
                        builder.destination.pop(0)
                    builder.destination.append(random.choice(self.graph.freeGroundNodes))
                    if builder.destination[0] in self.graph.freeGroundNodes:
                        self.graph.freeGroundNodes.remove(builder.destination[0])
                        builder.destination.append(Enumerations.location_type.kiln)  # add it's location if found
                    else:  # if not found, make destination empty again
                        while len(builder.destination) > 0:
                            builder.destination.pop(0)

                    if len(builder.destination) > 0:  # if kiln found, start building
                        self.needKiln = False
                        builder.stateMachine.changeState(self.states.build)
                    else:  # if destination not found, set to idle
                        builder.stateMachine.changeState(self.states.idle)

        # make all free trees request to be chopped
        for tree in self.trees:
            if self.trees[tree].owner is None and tree not in self.graph.fogNodes:

                # if heuristic <= self.maxDistanceTreeFromWorker, break. A close worker has been found.
                shortestDistance = 100000000000000000000
                closestWorker = None
                if not self.trees[tree].searchFurtherAway:
                    for worker in self.entityManager.workers:
                        newDistance = Algorithms.heuristic(tree, worker.pos)
                        if not worker.isWorking and newDistance <= self.closeDistanceTreeFromWorker and \
                                worker not in self.entityManager.isUpgrading:
                            while len(worker.destination) > 0:
                                worker.destination.pop(0)
                            worker.destination.append(tree)
                            worker.destination.append(Enumerations.location_type.tree)
                            self.trees[tree].owner = worker
                            worker.stateMachine.changeState(self.states.chopTree)
                            closestWorker = worker
                            break
                        elif not worker.isWorking and newDistance < shortestDistance and \
                                worker not in self.entityManager.isUpgrading:
                            shortestDistance = newDistance

                else:  # search further away
                    self.trees[tree].searchFurtherAway = False
                    for worker in self.entityManager.workers:
                        newDistance = Algorithms.heuristic(tree, worker.pos)
                        if not worker.isWorking and newDistance <= self.maxDistanceTreeFromWorker and \
                                worker not in self.entityManager.isUpgrading:
                            while len(worker.destination) > 0:
                                worker.destination.pop(0)
                            worker.destination.append(tree)
                            worker.destination.append(Enumerations.location_type.tree)
                            self.trees[tree].owner = worker
                            worker.stateMachine.changeState(self.states.chopTree)
                            closestWorker = worker
                            break
                        elif not worker.isWorking and newDistance < shortestDistance and \
                                worker not in self.entityManager.isUpgrading:
                            shortestDistance = newDistance
                            closestWorker = worker

                # if closest found worker is further away than self.maxDistanceTreeFromWorker, set it to owner
                if closestWorker is not None:  # if found after all searches above
                    while len(closestWorker.destination) > 0:
                        closestWorker.destination.pop(0)
                    closestWorker.destination.append(tree)
                    closestWorker.destination.append(Enumerations.location_type.tree)
                    self.trees[tree].owner = closestWorker
                    closestWorker.stateMachine.changeState(self.states.chopTree)
                else:
                    self.trees[tree].searchFurtherAway = True

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

            while self.iterationsSoFar <= self.pathIterationsPerUpdate:
                if len(self.craftsmanAStarPriorityQ) == 0:
                    self.craftsmanPathsToFind[0][1][0].route = [(0, 0)]
                    self.craftsmanAStarPriorityQ.clear()
                    self.craftsmanAStarPath.clear()
                    self.craftsmanAStarCostSoFar.clear()
                    heapq.heappop(self.craftsmanPathsToFind)[1]
                    if len(self.craftsmanPathsToFind) > 0:
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
                        (self.craftsmanPathsToFind[0][1][2], self.craftsmanPathsToFind[0][1][3],
                         self.craftsmanAStarPath)
                    self.craftsmanAStarPriorityQ.clear()
                    self.craftsmanAStarPath.clear()
                    self.craftsmanAStarCostSoFar.clear()
                    self.craftsmanPriorityQ.clear()
                    self.craftsmanPath.clear()
                    self.craftsmanCostSoFar.clear()
                    heapq.heappop(self.craftsmanPathsToFind)[1]
                    if len(self.craftsmanPathsToFind) > 0:
                        self.doPathFinding()
                    break

                for neighbour in self.craftsmanPathsToFind[0][1][1].neighboursExceptFog(currentNode):
                    newCost = self.craftsmanAStarCostSoFar[currentNode] + \
                              Algorithms.tileDependentHeuristic \
                                  (self.craftsmanPathsToFind[0][1][1], neighbour, currentNode, self.moveVariables)
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

        elif len(self.pathsToFind) > 0 and self.pathsFoundForWorkers <= self.workerPathsPerDiscoverer:
            # 0:entity, 1:graph, 2:start, 3:goal
            goalIsValid = True
            if len(self.pathsToFind[0][1][0].destination) > 0:
                if self.pathsToFind[0][1][0].destination[1] == Enumerations.location_type.builder:
                    builderFound = False
                    for builder in self.entityManager.builders:
                        if builder.pos == self.pathsToFind[0][1][3]:
                            builderFound = True
                            break
                    if not builderFound:
                        goalIsValid = False

            if not goalIsValid:
                if len(self.pathsToFind[0][1][0].destination) > 0:
                    # entity might have more destinations in the list (it shouldn't though)
                    for index in range(2):  # only removes the first destination, which goal was invalid
                        # but the first destination might not be the one that's shortest
                        self.pathsToFind[0][1][0].destination.pop(0)
                self.AStarPriorityQ.clear()
                self.AStarPath.clear()
                self.AStarCostSoFar.clear()
                self.priorityQ.clear()
                self.path.clear()
                self.costSoFar.clear()
                heapq.heappop(self.pathsToFind)[1]
                self.pathsFoundForWorkers = 0
                if len(self.pathsToFind) > 0:
                    self.doPathFinding()
                self.iterationsSoFar = 0

            else:
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

                while self.iterationsSoFar <= self.pathIterationsPerUpdate:
                    if len(self.AStarPriorityQ) == 0:
                        self.pathsToFind[0][1][0].route = [(0, 0)]
                        self.AStarPriorityQ.clear()
                        self.AStarPath.clear()
                        self.AStarCostSoFar.clear()
                        heapq.heappop(self.pathsToFind)[1]
                        if self.pathsFoundForWorkers > self.workerPathsPerDiscoverer:
                            self.pathsFoundForWorkers = 0
                        else:
                            self.pathsFoundForWorkers += 1
                        if len(self.pathsToFind) > 0:
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
                        if self.pathsFoundForWorkers > self.workerPathsPerDiscoverer:
                            self.pathsFoundForWorkers = 0
                        else:
                            self.pathsFoundForWorkers += 1
                        if len(self.pathsToFind) > 0:
                            self.doPathFinding()
                        break

                    for neighbour in self.pathsToFind[0][1][1].neighboursExceptFog(currentNode):
                        newCost = self.AStarCostSoFar[currentNode] + \
                                  Algorithms.tileDependentHeuristic \
                                      (self.pathsToFind[0][1][1], neighbour, currentNode, self.moveVariables)
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
            # if goal is not in fogNodes, set discoverer's nextFogNode to None and remove this discovererPathToFind
            if self.discoverPathsToFind[0][1][3] not in self.graph.fogNodes:
                self.discoverPathsToFind[0][1][0].variables["nextFogNode"] = None
                if self.discoverPathsToFind[0][1][3] in self.graph.occupiedNodes:
                    self.graph.occupiedNodes.remove(self.discoverPathsToFind[0][1][3])
                for neighbour in self.graph.neighbours(self.discoverPathsToFind[0][1][3]):
                    if neighbour in self.graph.occupiedNodes:
                        self.graph.occupiedNodes.remove(neighbour)
                self.discoverAStarPriorityQ.clear()
                self.discoverAStarPath.clear()
                self.discoverAStarCostSoFar.clear()
                self.discoverPriorityQ.clear()
                self.discoverPath.clear()
                self.discoverCostSoFar.clear()
                heapq.heappop(self.discoverPathsToFind)[1]
                self.pathsFoundForWorkers = 0
                if len(self.discoverPathsToFind) > 0:
                    self.doPathFinding()
                self.iterationsSoFar = 0

            else:
                if len(self.discoverPriorityQ) == 0:  # new entity
                    self.discoverAStarPriorityQ.clear()
                    heapq.heappush(self.discoverAStarPriorityQ, (0, tuple(self.discoverPathsToFind[0][1][2])))
                    self.discoverAStarPath[tuple(self.discoverPathsToFind[0][1][2])] = None
                    self.discoverAStarCostSoFar[tuple(self.discoverPathsToFind[0][1][2])] = 0
                else:  # set A* variables to progress values
                    self.discoverAStarPriorityQ = self.discoverPriorityQ
                    self.discoverAStarPath = self.discoverPath
                    self.discoverAStarCostSoFar = self.discoverCostSoFar

                while self.iterationsSoFar <= self.pathIterationsPerUpdate:
                    if len(self.discoverAStarPriorityQ) == 0:  # return an invalid tuple if no path found
                        self.discoverPathsToFind[0][1][0].route = [(0, 0)]
                        self.discoverAStarPriorityQ.clear()
                        self.discoverAStarPath.clear()
                        self.discoverAStarCostSoFar.clear()
                        heapq.heappop(self.discoverPathsToFind)[1]
                        self.pathsFoundForWorkers = 0
                        if len(self.discoverPathsToFind) > 0:
                            self.doPathFinding()
                        break

                    currentNode = heapq.heappop(self.discoverAStarPriorityQ)[1]

                    if currentNode == tuple(self.discoverPathsToFind[0][1][3]):
                        if self.discoverAStarPath[self.discoverPathsToFind[0][1][2]] is not None:
                            print("will get an error :((")
                        self.discoverPathsToFind[0][1][0].route = Algorithms.getRoute \
                            (self.discoverPathsToFind[0][1][2], self.discoverPathsToFind[0][1][3],
                             self.discoverAStarPath)
                        self.discoverAStarPriorityQ.clear()
                        self.discoverAStarPath.clear()
                        self.discoverAStarCostSoFar.clear()
                        self.discoverPriorityQ.clear()
                        self.discoverPath.clear()
                        self.discoverCostSoFar.clear()
                        heapq.heappop(self.discoverPathsToFind)[1]
                        self.pathsFoundForWorkers = 0
                        if len(self.discoverPathsToFind) > 0:
                            self.doPathFinding()
                        break

                    for neighbour in self.discoverPathsToFind[0][1][1].neighbours(currentNode):
                        newCost = self.discoverAStarCostSoFar[currentNode] + \
                                  Algorithms.tileDependentHeuristic \
                                      (self.discoverPathsToFind[0][1][1], neighbour, currentNode, self.moveVariables)
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

        else:
            self.pathsFoundForWorkers = 0
