import Enumerations
import Algorithms
import random


class States:
    def __init__(self):
        States.wandering = Wandering()
        States.upgradingToDiscoverer = UpgradingToDiscoverer()
        States.discover = Discover()
        States.idle = Idle()


class Wandering:
    def __init__(self):
        self.directions = [(-1, -1), (0, -1), (1, -1),
                           (-1, 0), (1, 0),
                           (-1, 1), (0, 1), (1, 1)]

    def enter(self, character):
        pass

    def update(self, character):
        randomDirection = random.choice(self.directions)
        newPos = (character.pos[0] + randomDirection[0], character.pos[1] + randomDirection[1])
        if newPos in character.entityManager.worldManager.graph.fogNodes or \
                newPos in character.entityManager.worldManager.graph.nonWalkables:
            pass
        else:
            character.move(newPos, character.entityManager.worldManager.graph)

        # if route is None, get random point on map, A* to that point
        # if len(character.route) <= 0:
        #     randomPoint = random.choice(character.entityManager.worldManager.graph.groundNodes)
        #     while randomPoint in character.entityManager.worldManager.graph.occupiedNodes:
        #         randomPoint = random.choice(character.entityManager.worldManager.graph.groundNodes)
        #     path = Algorithms.findPathToNode(character.entityManager.worldManager.graph, character.pos, randomPoint)
        #     character.route = Algorithms.getRoute(character.pos, randomPoint, path)
        #
        # # else move to route
        # else:
        #     # if route[0] is in fogNodes, don't move
        #     # if workers are in route[0], don't move.
        #     if character.route[0] not in character.entityManager.worldManager.graph.fogNodes:
        #         character.move(character.route[0], character.entityManager.worldManager.graph)
        #         character.route.pop(0)
        #     else:
        #         pass

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
    def enter(self, character):
        pass

    def update(self, character):
        # remove fog
        if character.pos in character.entityManager.worldManager.graph.fogNodes:

            # tell workers the tree is cleared of fog
            if character.pos in character.entityManager.worldManager.graph.treeNodes:
                for entity in character.entityManager.workers:
                    character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                        (character, entity, Enumerations.message_type.treeAppeared, 0, character.pos)

            character.entityManager.worldManager.graph.fogNodes.remove(character.pos)

        for neighbour in character.entityManager.worldManager.graph.neighbours(character.pos):
            if neighbour in character.entityManager.worldManager.graph.fogNodes:

                if neighbour in character.entityManager.worldManager.graph.treeNodes:
                    for entity in character.entityManager.workers:
                        character.entityManager.worldManager.messageDispatcher.dispatchMessage \
                            (character, entity, Enumerations.message_type.treeAppeared, 0, neighbour)

                character.entityManager.worldManager.graph.fogNodes.remove(neighbour)

        if character.variables["nextFogNode"] is None:
            # find next fogNode
            # TODO: use BFS first, then random point with A*
            character.variables["nextFogNode"] = Algorithms.findNearestRandomFogNode \
                (character.entityManager.worldManager.graph)
            if character.variables["nextFogNode"] is None or \
                    len(character.entityManager.worldManager.graph.occupiedNodes) == \
                    len(character.entityManager.worldManager.graph.fogNodes):
                character.stateMachine.changeState(States.idle)

            else:
                character.entityManager.worldManager.graph.occupiedNodes.append(character.variables["nextFogNode"])
                path = Algorithms.findPathToNode \
                    (character.entityManager.worldManager.graph, character.pos, character.variables["nextFogNode"])
                character.route = Algorithms.getRoute(character.pos, character.variables["nextFogNode"], path)

        else:
            # get movin' to tha node
            character.move(character.route[0], character.entityManager.worldManager.graph)
            character.route.pop(0)
            if len(character.route) <= 0:
                character.entityManager.worldManager.graph.occupiedNodes.remove(character.variables["nextFogNode"])
                character.variables["nextFogNode"] = None

    def exit(self, character):
        pass


class Idle:
    def enter(self, character):
        pass

    def update(self, character):
        pass

    def exit(self, character):
        pass
