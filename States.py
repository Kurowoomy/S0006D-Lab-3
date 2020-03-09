import Enumerations
import Algorithms
import random
import heapq


class States:
    def __init__(self):
        States.wandering = Wandering()
        States.upgradingToDiscoverer = UpgradingToDiscoverer()
        States.discover = Discover()
        States.idle = Idle()
        States.moveToDestination = MoveToDestination()
        States.chopTree = ChopTree()
        States.carryTree = CarryTree()
        States.upgradingToBuilder = UpgradingToBuilder()
        States.build = Build()
        States.upgradingToKilnManager = UpgradingToKilnManager()
        States.manageKiln = ManageKiln()


class Wandering:
    def __init__(self):
        self.directions = [(-1, -1), (0, -1), (1, -1),
                           (-1, 0), (1, 0),
                           (-1, 1), (0, 1), (1, 1)]

    def enter(self, character):
        character.isWorking = False

    def update(self, character):
        randomDirection = random.choice(self.directions)
        newPos = (character.pos[0] + randomDirection[0], character.pos[1] + randomDirection[1])
        if newPos in character.entityManager.worldManager.graph.fogNodes or \
                newPos in character.entityManager.worldManager.graph.nonWalkables:
            pass
        else:
            character.move(newPos, character.entityManager.worldManager.graph)

    def exit(self, character):
        pass


class UpgradingToDiscoverer:
    def __init__(self):
        self.isInFog = False

    def enter(self, character):
        character.entityManager.isUpgrading.append(character)
        character.entityManager.worldManager.messageDispatcher.dispatchMessage \
            (character, character, Enumerations.message_type.isUpgradedDiscoverer,
             character.entityVariables["discovererUpgradeTime"], None)

    def update(self, character):
        # if no fog is near anymore, dispatchMessage(self, self.worldManager, stopUpgrading, 0, None)
        # check if neighbours are in fog
        neighbours = character.entityManager.worldManager.graph.neighbours(character.pos)

        self.isInFog = False
        for neighbour in neighbours:
            if neighbour in character.entityManager.worldManager.graph.fogNodes:
                self.isInFog = True

        if not self.isInFog:
            character.entityManager.isUpgrading.remove(character)
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character.entityManager.worldManager, character, Enumerations.message_type.stopUpgrading, 0, None)
            character.stateMachine.changeState(States.wandering)
        # if amount of discoverers has reached maxDiscovererAmount, stopUpgrading
        elif len(character.entityManager.discoverers) >= character.entityManager.worldManager.maxDiscovererAmount:
            character.entityManager.isUpgrading.remove(character)
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character.entityManager.worldManager, character, Enumerations.message_type.stopUpgrading, 0, None)
            character.stateMachine.changeState(States.wandering)

    def exit(self, character):
        pass


class Discover:
    def __init__(self):
        self.nodeHasWorker = False

    def enter(self, character):
        pass

    def update(self, character):
        # remove fog
        if character.variables["hasMoved"]:
            character.variables["hasMoved"] = False
            if character.pos in character.entityManager.worldManager.graph.fogNodes:
                if character.pos in character.entityManager.worldManager.graph.occupiedNodes:
                    character.entityManager.worldManager.graph.occupiedNodes.remove(character.pos)

                character.entityManager.worldManager.graph.fogNodes.remove(character.pos)

                if character.pos in character.entityManager.worldManager.graph.groundNodes and \
                        character.pos not in character.entityManager.worldManager.graph.treeNodes:
                    character.entityManager.worldManager.graph.freeGroundNodes.append(character.pos)

            for neighbour in character.entityManager.worldManager.graph.neighbours(character.pos):
                if neighbour in character.entityManager.worldManager.graph.fogNodes:
                    if neighbour in character.entityManager.worldManager.graph.occupiedNodes:
                        character.entityManager.worldManager.graph.occupiedNodes.remove(neighbour)

                    character.entityManager.worldManager.graph.fogNodes.remove(neighbour)

                    if neighbour in character.entityManager.worldManager.graph.groundNodes and \
                            neighbour not in character.entityManager.worldManager.graph.treeNodes:
                        character.entityManager.worldManager.graph.freeGroundNodes.append(neighbour)
        else:
            # get path
            if character.variables["nextFogNode"] is None:
                if not character.entityManager.worldManager.AStarHasOccurred:
                    # find next fogNode
                    character.variables["nextFogNode"], path = Algorithms.findNearestFogNodeBFS \
                        (character.entityManager.worldManager.graph, character.pos,
                         character.entityVariables["maxLoopsForBFS"])

                    if character.variables["nextFogNode"] is None:
                        print("No path found. Discoverer with ID", character.ID, "is now idle")
                        character.variables["nextFogNode"] = None
                        character.route.clear()
                        character.stateMachine.changeState(States.idle)

                    else:  # if nextFogNode is found
                        character.entityManager.worldManager.graph.occupiedNodes.append(
                            character.variables["nextFogNode"])
                        # set neighbours to nextFogNode goal to occupiedNodes as well
                        for neighbour in \
                                character.entityManager.worldManager.graph.neighbours(
                                    character.variables["nextFogNode"]):
                            if neighbour in character.entityManager.worldManager.graph.fogNodes:
                                character.entityManager.worldManager.graph.occupiedNodes.append(neighbour)

                        # do path finding
                        # add character, graph, start and goal to pathsToFind in worldManager
                        if Algorithms.heuristic(character.variables["nextFogNode"], character.pos) <= \
                                character.entityVariables["maxDistanceNextFogNodeBFS"]:
                            character.route = Algorithms.getRoute \
                                (character.pos, character.variables["nextFogNode"],
                                 Algorithms.findPathToNode(character.entityManager.worldManager.graph, character.pos,
                                                           character.variables["nextFogNode"],
                                                           character.entityManager.worldManager.moveVariables))
                        else:  # if distance is more than maxDistanceNextFogNodeBFS, add to discoverPathsToFind
                            if len(character.entityManager.worldManager.discoverPathsToFind) > 0 and \
                                    len(character.entityManager.worldManager.discoverPriorityQ) > 0 and \
                                    Algorithms.heuristic(character.variables["nextFogNode"], character.pos) <= \
                                    character.entityManager.worldManager.discoverPathsToFind[0][0]:
                                character.entityManager.worldManager.discoverPriorityQ.clear()
                            heapq.heappush(character.entityManager.worldManager.discoverPathsToFind,
                                           (Algorithms.heuristic(character.variables["nextFogNode"], character.pos),
                                            [character, character.entityManager.worldManager.graph,
                                             character.pos, character.variables["nextFogNode"]]))

            else:
                # start moving to the node
                if len(character.route) <= 0:
                    pass  # waiting for doPathFinding to finish
                elif character.route[0] == (0, 0):
                    # trying to reach something that's surrounded by nonWalkables. Remove it from fogNodes and
                    # remove nextFogNode from occupied and its neighbours with fog
                    if character.variables["nextFogNode"] in character.entityManager.worldManager.graph.fogNodes:
                        character.entityManager.worldManager.graph.fogNodes.remove(character.variables["nextFogNode"])
                        if character.variables["nextFogNode"] in \
                                character.entityManager.worldManager.graph.occupiedNodes:
                            character.entityManager.worldManager.graph.occupiedNodes.remove(
                                character.variables["nextFogNode"])
                    for neighbour in character.entityManager.worldManager.graph.neighbours(
                            character.variables["nextFogNode"]):
                        if neighbour in character.entityManager.worldManager.graph.fogNodes:
                            character.entityManager.worldManager.graph.fogNodes.remove(neighbour)
                            if neighbour in character.entityManager.worldManager.graph.occupiedNodes:
                                character.entityManager.worldManager.graph.occupiedNodes.remove(neighbour)

                    print("No path found. Discoverer with ID", character.ID, "tries to find new fogNode")
                    character.variables["nextFogNode"] = None
                    character.route.clear()
                else:
                    character.variables["hasMoved"] = True
                    character.move(character.route[0], character.entityManager.worldManager.graph)
                    character.route.pop(0)
                    if len(character.route) <= 0:
                        character.variables["nextFogNode"] = None

    def exit(self, character):
        pass


class ChopTree:
    def enter(self, character):
        character.isWorking = True
        if character.destination[0] != character.pos:
            character.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, character)
            character.stateMachine.changeState(States.moveToDestination)
        else:
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.treeIsChopped,
                 character.entityVariables["treeChopTime"],
                 character.entityManager.worldManager.trees[character.destination[0]])
            character.destination.pop(0)
            character.destination.pop(0)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class CarryTree:
    def enter(self, character):
        character.isWorking = True
        if character.destination[0] != character.pos:
            character.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, character)
            character.stateMachine.changeState(States.moveToDestination)
        else:  # do the same as in move-message -> kiln destination is reached
            print("worker is already at kiln")
            for kilnManager in character.entityManager.kilnManagers:
                if kilnManager.pos == character.pos:
                    character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (kilnManager, character, Enumerations.message_type.recieveMaterial, 0, \
                         character.variables["item"])
            while len(character.destination) > 0:
                character.destination.pop(0)
            character.stateMachine.changeState(States.wandering)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class MoveToDestination:
    def enter(self, character):
        if len(character.route) <= 0:
            if not character.entityManager.worldManager.AStarHasOccurred:
                if character.occupation == "kilnManager" or character.occupation == "builder":
                    if len(character.entityManager.worldManager.craftsmanPathsToFind) > 0 and \
                            len(character.entityManager.worldManager.craftsmanPriorityQ) > 0 and \
                            Algorithms.heuristic(character.destination[0], character.pos) <= \
                            character.entityManager.worldManager.craftsmanPathsToFind[0][0]:
                        character.entityManager.worldManager.craftsmanPriorityQ.clear()
                    heapq.heappush(character.entityManager.worldManager.craftsmanPathsToFind,
                                   (Algorithms.heuristic(character.destination[0], character.pos),
                                    [character, character.entityManager.worldManager.graph,
                                     character.pos, character.destination[0]]))
                else:
                    if len(character.entityManager.worldManager.pathsToFind) > 0 and \
                            len(character.entityManager.worldManager.priorityQ) > 0 and \
                            Algorithms.heuristic(character.destination[0], character.pos) <= \
                            character.entityManager.worldManager.pathsToFind[0][0]:
                        character.entityManager.worldManager.priorityQ.clear()
                    heapq.heappush(character.entityManager.worldManager.pathsToFind,
                                   (Algorithms.heuristic(character.destination[0], character.pos),
                                    [character, character.entityManager.worldManager.graph,
                                     character.pos, character.destination[0]]))

    def update(self, character):
        if len(character.route) <= 0:
            pass  # wait for doPathFinding to finish
        elif character.route[0] == (0, 0):
            print("No path found")
            # if this character still owns the location, release it
            if character.destination[1] == Enumerations.location_type.tree and \
                    character.entityManager.worldManager.trees[character.destination[0]].owner == character:
                character.entityManager.worldManager.trees[character.destination[0]].owner = None
            elif character.destination[1] == Enumerations.location_type.kiln and \
                    character.entityManager.worldManager.buildings[character.destination[0]].owner == character:
                character.entityManager.worldManager.buildings[character.destination[0]].owner = None

            while len(character.destination) > 0:
                character.destination.pop(0)
            character.route.clear()
            character.stateMachine.changeState(States.idle)
        else:
            character.move(character.route[0], character.entityManager.worldManager.graph)  # goes to idle state
            character.route.pop(0)

    def exit(self, character):
        pass


class UpgradingToBuilder:
    def enter(self, character):
        character.entityManager.isUpgrading.append(character)
        character.entityManager.worldManager.messageDispatcher.dispatchMessage \
            (character, character, Enumerations.message_type.isUpgradedBuilder,
             character.entityVariables["craftsManUpgradeTime"], None)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class Build:
    def enter(self, character):
        character.isWorking = True
        if character.destination[0] != character.pos:
            character.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, character)
            character.stateMachine.changeState(States.moveToDestination)
        else:
            character.destination.pop(0)
            character.destination.pop(0)
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.buildingIsDone,
                 character.entityVariables["timePerBuilding"], None)
            character.stateMachine.changeState(States.idle)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class UpgradingToKilnManager:
    def enter(self, character):
        character.entityManager.isUpgrading.append(character)
        character.entityManager.worldManager.messageDispatcher.dispatchMessage \
            (character, character, Enumerations.message_type.isUpgradedKilnManager,
             character.entityVariables["craftsManUpgradeTime"], None)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class ManageKiln:
    def enter(self, character):
        character.isWorking = True
        if character.destination[0] != character.pos:
            character.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, character)
            character.stateMachine.changeState(States.moveToDestination)
        else:
            character.destination.pop(0)
            character.destination.pop(0)
            # tell workers with a tree that they can start carryTree
            # the workers must not stand on a tree (why? I forgot)
            # I changed it to worker must not have a destination, just like in update
            for worker in character.entityManager.workers:
                if worker.variables["item"] is not None and len(worker.destination) <= 0:
                    worker.destination.append(character.pos)
                    worker.destination.append(Enumerations.location_type.kiln)
                    worker.stateMachine.changeState(States.carryTree)

    def update(self, character):
        # if is at kiln and is its owner, check charcoal requirements
        # if enough trees in variable["items"], send message to itself to make charchoal
        if len(character.variables["items"]) >= character.entityVariables["treesPerCharcoal"] and \
                not character.variables["isMakingCharcoal"]:
            character.variables["isMakingCharcoal"] = True
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.charcoalIsDone,
                 character.entityVariables["timePerCharcoal"], None)
        else:  # giveMeTrees
            for worker in character.entityManager.workers:
                # a worker who has a tree but no destination
                if worker.variables["item"] is not None and len(worker.destination) <= 0:
                    character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (worker, character, Enumerations.message_type.giveMeTrees, 0, None)

    def exit(self, character):
        pass


class Idle:
    def enter(self, character):
        pass

    def update(self, character):
        pass

    def exit(self, character):
        pass
