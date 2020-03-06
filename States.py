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
            (character, character, Enumerations.message_type.isUpgradedDiscoverer, 5, None)

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
        pass

    def exit(self, character):
        pass


class Discover:
    def __init__(self):
        self.nodeHasWorker = False

    def enter(self, character):
        pass

    def update(self, character):
        # remove fog
        if character.pos in character.entityManager.worldManager.graph.fogNodes:

            character.entityManager.worldManager.graph.fogNodes.remove(character.pos)
            # tell workers the tree is cleared of fog
            # if character.pos in character.entityManager.worldManager.trees:
            #     for entity in character.entityManager.workers:
            #         if entity not in character.entityManager.isUpgrading and not entity.isWorking and \
            #                 entity.variables["item"] is None:
            #             character.entityManager.worldManager.messageDispatcher.dispatchMessage \
            #                 (entity, character, Enumerations.message_type.treeAppeared, 0, character.pos)
            #
            # else:
            if character.pos in character.entityManager.worldManager.graph.groundNodes:
                character.entityManager.worldManager.graph.freeGroundNodes.append(character.pos)

        for neighbour in character.entityManager.worldManager.graph.neighbours(character.pos):
            if neighbour in character.entityManager.worldManager.graph.fogNodes:

                character.entityManager.worldManager.graph.fogNodes.remove(neighbour)
                # if neighbour in character.entityManager.worldManager.trees:
                #     for entity in character.entityManager.workers:
                #         if entity not in character.entityManager.isUpgrading and not entity.isWorking and \
                #                 entity.variables["item"] is None:
                #             character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                #                 (entity, character, Enumerations.message_type.treeAppeared, 0, neighbour)

                # else:
                if neighbour in character.entityManager.worldManager.graph.groundNodes:
                    character.entityManager.worldManager.graph.freeGroundNodes.append(neighbour)

        # get path
        if character.variables["nextFogNode"] is None:
            if not character.entityManager.worldManager.AStarHasOccurred:
                # find next fogNode
                character.variables["nextFogNode"], path = Algorithms.findNearestFogNodeBFS \
                    (character.entityManager.worldManager.graph, character.pos)

                if character.variables["nextFogNode"] is None or \
                        len(character.entityManager.worldManager.graph.occupiedNodes) == \
                        len(character.entityManager.worldManager.graph.fogNodes):
                    pass

                else:  # if nextFogNode is found
                    character.entityManager.worldManager.graph.occupiedNodes.append(character.variables["nextFogNode"])
                    # do path finding
                    # add character, graph, start and goal to pathsToFind in worldManager
                    if Algorithms.heuristic(character.variables["nextFogNode"], character.pos) <= 72:
                        character.route = Algorithms.getRoute \
                            (character.pos, character.variables["nextFogNode"],
                             Algorithms.findPathToNode(character.entityManager.worldManager.graph, character.pos,
                                                       character.variables["nextFogNode"]))
                    else:
                        # gör en heapq push med heuristic distance som sorterare/prioritet
                        # TODO: eventuellt ta bort paths för discoverers där dimman inte längre finns
                        # if len(character.entityManager.worldManager.pathsToFind) > 0 and \
                        #         len(character.entityManager.worldManager.priorityQ) > 0 and \
                        #         Algorithms.heuristic(character.variables["nextFogNode"], character.pos) <= \
                        #         character.entityManager.worldManager.pathsToFind[0][0]:
                        #     character.entityManager.worldManager.discoverPathsToFind.append \
                        #         ((Algorithms.heuristic(character.variables["nextFogNode"], character.pos),
                        #           [character, character.entityManager.worldManager.graph,
                        #            character.pos, character.variables["nextFogNode"]]))
                        # else:
                            # if len(character.entityManager.worldManager.pathsToFind) > 0 and \
                            #         character.entityManager.worldManager.pathsToFind[0][1][
                            #             0].occupation != "discoverer":
                            #     character.entityManager.worldManager.pathsToFind.append \
                            #         ((Algorithms.heuristic(character.variables["nextFogNode"], character.pos),
                            #           [character, character.entityManager.worldManager.graph,
                            #            character.pos, character.variables["nextFogNode"]]))
                            # else:
                        if len(character.entityManager.worldManager.discoverPathsToFind) > 0 and \
                                len(character.entityManager.worldManager.discoverPriorityQ) > 0 and \
                                Algorithms.heuristic(character.variables["nextFogNode"], character.pos) <= \
                                character.entityManager.worldManager.discoverPathsToFind[0][0]:
                            character.entityManager.worldManager.discoverPriorityQ.clear()
                        heapq.heappush(character.entityManager.worldManager.discoverPathsToFind,
                                           (Algorithms.heuristic(character.variables["nextFogNode"], character.pos),
                                            [character, character.entityManager.worldManager.graph,
                                             character.pos, character.variables["nextFogNode"]]))
                        # character.entityManager.worldManager.pathsToFind.append\
                        #     ([character, character.entityManager.worldManager.graph,
                        #       character.pos, character.variables["nextFogNode"]])
                    # path = Algorithms.findPathToNode \
                    #    (character.entityManager.worldManager.graph, character.pos, character.variables["nextFogNode"])
                    # character.entityManager.worldManager.AStarHasOccurred = False
                    # character.route = Algorithms.getRoute(character.pos, character.variables["nextFogNode"], path)

        else:
            # get movin' to tha node
            if len(character.route) <= 0:
                pass  # waiting for doPathFinding to finish
            elif character.route[0] == (0, 0):
                print("No path found")
                character.variables["nextFogNode"] = None
                character.route.clear()
                character.stateMachine.changeState(States.idle)
            else:
                character.move(character.route[0], character.entityManager.worldManager.graph)
                character.route.pop(0)
                if len(character.route) <= 0:
                    character.entityManager.worldManager.graph.occupiedNodes.remove(character.variables["nextFogNode"])
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
            # remove all move messages
            # character.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, character)
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.treeIsChopped, 10,
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
            # route is popped when move message is sent, so it can't be used/saved for later
            # do I check inside the remove function? If entity's route
            character.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, character)
            # move message node isn't specified so when route updates it removes the first node of the new route :(
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
                # do path finding
                # add character, graph, start and goal to pathsToFind in worldManager
                # if Algorithms.heuristic(character.destination[0], character.pos < pathsToFind[0][0]:
                # then don't add it at the front..? I guess I'll use the normal append for this case
                # if it's not a discoverer,
                # if len(character.entityManager.worldManager.pathsToFind) > 0 and \
                #         len(character.entityManager.worldManager.priorityQ) > 0 and \
                #         Algorithms.heuristic(character.destination[0], character.pos) <= \
                #         character.entityManager.worldManager.pathsToFind[0][0]:
                #     character.entityManager.worldManager.pathsToFind.append \
                #         ((Algorithms.heuristic(character.destination[0], character.pos),
                #           [character, character.entityManager.worldManager.graph,
                #            character.pos, character.destination[0]]))
                # else:  # om en discoverer har kortare path än en worker som ligger först, så kommer den ta över första platsen :(
                    # lägg till discoverern via append om första path:en inte är en discoverer
                    # if character.occupation == "discoverer" and \
                    #         len(character.entityManager.worldManager.pathsToFind) > 0 and \
                    #         character.entityManager.worldManager.pathsToFind[0][1][0].occupation != "discoverer":
                    #     character.entityManager.worldManager.pathsToFind.append \
                    #         ((Algorithms.heuristic(character.destination[0], character.pos),
                    #           [character, character.entityManager.worldManager.graph,
                    #            character.pos, character.destination[0]]))
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
                # character.entityManager.worldManager.pathsToFind.append \
                #     ([character, character.entityManager.worldManager.graph,
                #       character.pos, character.destination[0]])
                # path = Algorithms.findPathAvoidFog \
                #     (character.entityManager.worldManager.graph, character.pos, character.destination[0])
                # character.entityManager.worldManager.AStarHasOccurred = False
                # character.route = Algorithms.getRoute(character.pos, character.destination[0], path)

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
            (character, character, Enumerations.message_type.isUpgradedBuilder, 5, None)

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
            # character.entityManager.worldManager.gatheredTreesAvailable -= 1
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.buildingIsDone, 5, None)
            character.stateMachine.changeState(States.idle)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class UpgradingToKilnManager:
    def enter(self, character):
        character.entityManager.isUpgrading.append(character)
        character.entityManager.worldManager.messageDispatcher.dispatchMessage \
            (character, character, Enumerations.message_type.isUpgradedKilnManager, 5, None)

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
            # the workers must not stand on a tree
            for worker in character.entityManager.workers:
                if worker.variables["item"] is not None and \
                        worker.pos not in character.entityManager.worldManager.trees:
                    worker.destination.append(character.pos)
                    worker.destination.append(Enumerations.location_type.kiln)
                    worker.stateMachine.changeState(States.carryTree)

    def update(self, character):
        # if is at kiln and is its owner, check charcoal requirements
        # if enough trees in variable["items"], send message to itself to make charchoal
        # if character.pos in character.entityManager.worldManager.buildings and \
        #         character.entityManager.worldManager.buildings[character.pos].owner is character:
        if len(character.variables["items"]) >= 1 and not character.variables["isMakingCharcoal"]:
            character.variables["isMakingCharcoal"] = True
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.charcoalIsDone, 5, None)
        else:  # giveMeTrees
            for worker in character.entityManager.workers:
                # if worker.variables["item"] is not None and \
                #         worker.stateMachine.currentState is not States.carryTree and \
                #         worker.stateMachine.currentState is not States.chopTree and \
                #         len(worker.destination) <= 0:  # or destination == character.pos
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
