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
        self.trees = {}
        self.buildings = {}
        self.messageDispatcher = MessageSystem.MessageDispatcher()
        self.states = States.States()
        self.needDiscoverers = True
        self.needBuilders = True
        self.needKilnManager = True
        self.gatheredTreesAvailable = 0
        self.needKiln = True
        self.AStarHasOccurred = False
        self.charcoal = 0
        self.buildingSpots = [(72, 90), (23, 90), (72, 37), (26, 11)]
        # path finding
        self.pathsToFind = []
        self.iterationsPerUpdate = 20
        self.iterationsSoFar = 0
        self.costSoFar = {}
        self.AStarCostSoFar = {}
        self.priorityQ = []
        self.AStarPriorityQ = []
        self.path = {}
        self.AStarPath = {}

    def update(self):
        # upgrading to builder and kilnManager
        if self.gatheredTreesAvailable >= 0 and self.needBuilders:
            for entity in self.entityManager.workers:
                if not entity.isWorking and entity not in self.entityManager.isUpgrading:
                    entity.stateMachine.changeState(self.states.upgradingToBuilder)
                    self.needBuilders = False
                    break
        if self.gatheredTreesAvailable >= 0 and self.needKilnManager:
            for entity in self.entityManager.workers:
                if not entity.isWorking and entity not in self.entityManager.isUpgrading:
                    entity.stateMachine.changeState(self.states.upgradingToKilnManager)
                    self.needKilnManager = False
                    break

        # make all free trees request to be chopped
        for tree in self.trees:
            if self.trees[tree].owner is None and tree not in self.graph.fogNodes:

                # if heuristic <= 72, break. A close worker has been found.
                shortestDistance = 100000000000000000000
                closestWorker = None
                for worker in self.entityManager.workers:
                    newDistance = Algorithms.heuristic(tree, worker.pos)
                    if not worker.isWorking and newDistance <= 100:
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
            for tree in self.trees:  # TODO: are dictionaries iterable?
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
                self.messageDispatcher.priorityQ.remove(message)

    def doPathFinding(self):
        if len(self.pathsToFind) > 0:  # 0:entity, 1:graph, 2:start, 3:goal

            if self.pathsToFind[0][1][0].occupation == "discoverer":
                if len(self.priorityQ) == 0:  # new entity
                    self.AStarPriorityQ.clear()
                    heapq.heappush(self.AStarPriorityQ, (0, tuple(self.pathsToFind[0][1][2])))
                    self.AStarPath[tuple(self.pathsToFind[0][1][2])] = None
                    self.AStarCostSoFar[tuple(self.pathsToFind[0][1][2])] = 0
                else:  # set A* variables to progress values
                    self.AStarPriorityQ = self.priorityQ
                    self.AStarPath = self.path
                    self.AStarCostSoFar = self.costSoFar

                while self.iterationsSoFar <= self.iterationsPerUpdate:
                    if len(self.AStarPriorityQ) == 0:  # return an invalid tuple if no path found
                        self.pathsToFind[0][1][0].route = [(0, 0)]
                        self.AStarPriorityQ.clear()
                        self.AStarPath.clear()
                        self.AStarCostSoFar.clear()
                        heapq.heappop(self.pathsToFind)[1]
                        # self.pathsToFind.pop(0)
                        if len(self.pathsToFind) > 0:
                            self.doPathFinding()
                        break

                    currentNode = heapq.heappop(self.AStarPriorityQ)[1]

                    if currentNode == tuple(self.pathsToFind[0][1][3]):
                        if currentNode == self.pathsToFind[0][1][2]:
                            print("will get an error :((")
                        self.pathsToFind[0][1][0].route = Algorithms.getRoute \
                            (self.pathsToFind[0][1][2], self.pathsToFind[0][1][3], self.AStarPath)
                        self.AStarPriorityQ.clear()
                        self.AStarPath.clear()
                        self.AStarCostSoFar.clear()
                        heapq.heappop(self.pathsToFind)[1]
                        if len(self.pathsToFind) > 0:
                            self.doPathFinding()
                        break

                    for neighbour in self.pathsToFind[0][1][1].neighbours(currentNode):
                        newCost = self.AStarCostSoFar[currentNode] + \
                                  Algorithms.tileDependentHeuristic(self.pathsToFind[0][1][1], neighbour, currentNode)
                        if (tuple(neighbour) not in self.AStarCostSoFar) or \
                                (newCost < self.AStarCostSoFar[tuple(neighbour)]):
                            self.AStarCostSoFar[tuple(neighbour)] = newCost
                            priority = newCost + Algorithms.heuristic(self.pathsToFind[0][1][3], neighbour)
                            self.AStarPath[tuple(neighbour)] = currentNode
                            heapq.heappush(self.AStarPriorityQ, (priority, tuple(neighbour)))

                    self.iterationsSoFar += 1

                self.iterationsSoFar = 0
                self.priorityQ = self.AStarPriorityQ
                self.path = self.AStarPath
                self.costSoFar = self.AStarCostSoFar

            else:  # if entity is not discoverer, avoid fog
                if len(self.priorityQ) == 0:  # new entity
                    self.AStarPriorityQ.clear()
                    heapq.heappush(self.AStarPriorityQ, (0, tuple(self.pathsToFind[0][1][2])))
                    self.AStarPath[tuple(self.pathsToFind[0][1][2])] = None
                    self.AStarCostSoFar[tuple(self.pathsToFind[0][1][2])] = 0
                else:  # set A* variables to progress values
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
                        if len(self.pathsToFind) > 0:
                            self.doPathFinding()
                        break

                    self.iterationsSoFar += 1
                    currentNode = heapq.heappop(self.AStarPriorityQ)[1]

                    if currentNode == tuple(self.pathsToFind[0][1][3]):
                        self.pathsToFind[0][1][0].route = Algorithms.getRoute\
                            (self.pathsToFind[0][1][2], self.pathsToFind[0][1][3], self.AStarPath)
                        self.AStarPriorityQ.clear()
                        self.AStarPath.clear()
                        self.AStarCostSoFar.clear()
                        heapq.heappop(self.pathsToFind)[1]
                        # self.pathsToFind.pop(0)
                        if len(self.pathsToFind) > 0:
                            self.doPathFinding()
                        break

                    for neighbour in self.pathsToFind[0][1][1].neighboursExceptFog(currentNode):
                        if neighbour not in self.pathsToFind[0][1][1].fogNodes:
                            newCost = self.AStarCostSoFar[currentNode] + \
                                      Algorithms.tileDependentHeuristic\
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
