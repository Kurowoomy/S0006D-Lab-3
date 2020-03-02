import Enumerations
import Algorithms
import random


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


class Discover:  # TODO: fix lag when tree is discovered
    def __init__(self):
        self.nodeHasWorker = False

    def enter(self, character):
        pass

    def update(self, character):
        # remove fog
        if character.pos in character.entityManager.worldManager.graph.fogNodes:

            character.entityManager.worldManager.graph.fogNodes.remove(character.pos)
            # tell workers the tree is cleared of fog
            if character.pos in character.entityManager.worldManager.trees:
                for entity in character.entityManager.workers:
                    if entity not in character.entityManager.isUpgrading and not entity.isWorking and \
                            entity.variables["item"] is None:
                        character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                            (entity, character, Enumerations.message_type.treeAppeared, 0, character.pos)
                        break

            else:
                if character in character.entityManager.worldManager.graph.groundNodes:
                    character.entityManager.worldManager.graph.freeGroundNodes.append(character.pos)

        for neighbour in character.entityManager.worldManager.graph.neighbours(character.pos):
            if neighbour in character.entityManager.worldManager.graph.fogNodes:

                character.entityManager.worldManager.graph.fogNodes.remove(neighbour)
                if neighbour in character.entityManager.worldManager.trees:
                    for entity in character.entityManager.workers:
                        if entity not in character.entityManager.isUpgrading and not entity.isWorking and \
                                entity.variables["item"] is None:
                            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                                (entity, character, Enumerations.message_type.treeAppeared, 0, neighbour)
                            break
                else:
                    if neighbour in character.entityManager.worldManager.graph.groundNodes:
                        character.entityManager.worldManager.graph.freeGroundNodes.append(neighbour)

        # get path
        if character.variables["nextFogNode"] is None:
            if not character.entityManager.worldManager.AStarHasOccurred:
                # find next fogNode
                # TODO: use BFS first, then get random point
                character.variables["nextFogNode"] = Algorithms.findNearestFogNodeBFS \
                    (character.entityManager.worldManager.graph, character.pos)

                if character.variables["nextFogNode"] is None or \
                        len(character.entityManager.worldManager.graph.occupiedNodes) == \
                        len(character.entityManager.worldManager.graph.fogNodes):
                    character.stateMachine.changeState(States.idle)

                else:  # if nextFogNode is found
                    character.entityManager.worldManager.graph.occupiedNodes.append(character.variables["nextFogNode"])
                    path = Algorithms.findPathToNode \
                        (character.entityManager.worldManager.graph, character.pos, character.variables["nextFogNode"])
                    character.entityManager.worldManager.AStarHasOccurred = False
                    character.route = Algorithms.getRoute(character.pos, character.variables["nextFogNode"], path)
            else:
                pass

        else:
            # get movin' to tha node
            if len(character.route) <= 0:
                character.entityManager.worldManager.graph.occupiedNodes.remove(character.variables["nextFogNode"])
                character.variables["nextFogNode"] = None
                print("error occured here :(")
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
            character.entityManager.worldManager.removeAllMessagesOf(Enumerations.message_type.move, character)
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.treeIsChopped, 10, \
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
        else:
            character.destination.pop(0)
            character.destination.pop(0)
            for kilnManager in character.entityManager.kilnManagers:
                if kilnManager.pos == character.pos:
                    character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (kilnManager, character, Enumerations.message_type.recieveMaterial, 0, \
                         character.variable["item"])
                    character.variable["item"] = None
                    character.stateMachine.changeState(States.wandering)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class MoveToDestination:
    def enter(self, character):
        if len(character.route) <= 0:
            if not character.entityManager.worldManager.AStarHasOccurred:
                if character.occupation != "discoverer":
                    path = Algorithms.findPathAvoidFog \
                        (character.entityManager.worldManager.graph, character.pos, character.destination[0])
                else:
                    path = Algorithms.findPathToNode \
                        (character.entityManager.worldManager.graph, character.pos, character.destination[0])
                character.entityManager.worldManager.AStarHasOccurred = False
                character.route = Algorithms.getRoute(character.pos, character.destination[0], path)

    def update(self, character):
        if len(character.route) <= 0:
            if not character.entityManager.worldManager.AStarHasOccurred:
                if character.occupation != "discoverer":
                    path = Algorithms.findPathAvoidFog \
                        (character.entityManager.worldManager.graph, character.pos, character.destination[0])
                else:
                    path = Algorithms.findPathToNode \
                        (character.entityManager.worldManager.graph, character.pos, character.destination[0])
                character.entityManager.worldManager.AStarHasOccurred = False
                character.route = Algorithms.getRoute(character.pos, character.destination[0], path)
        else:
            character.move(character.route[0], character.entityManager.worldManager.graph)
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
            character.entityManager.worldManager.gatheredTreesAvailable -= 10
            character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                (character, character, Enumerations.message_type.buildingIsDone, 0, None)

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
            for worker in character.entityManager.workers:
                if worker.variables["item"] is not None:
                    worker.destination.append(character.pos)
                    worker.destination.append(Enumerations.location_type.kiln)
                    worker.stateMachine.changeState(States.carryTree)

    def update(self, character):
        # is at kiln
        # if enough trees in variable["items"], send message to itself to make charchoal
        for building in character.entityManager.worldManager.buildings:
            if character.pos == building:
                if len(character.variables["items"]) >= 2 and not character.variables["isMakingCharcoal"]:
                    character.variables["isMakingCharcoal"] = True
                    character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (character, character, Enumerations.message_type.charcoalIsDone, 5, None)
                break
        else:
            pass  # do nothing

    def exit(self, character):
        pass


class Idle:
    def enter(self, character):
        pass

    def update(self, character):
        pass

    def exit(self, character):
        pass
