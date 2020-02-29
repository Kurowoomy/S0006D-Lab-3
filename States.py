import Enumerations
import Algorithms


class States:
    def __init__(self):
        States.lookForTree = LookForTree()
        States.upgradingToDiscoverer = UpgradingToDiscoverer()
        States.discover = Discover()
        States.idle = Idle()


class LookForTree:
    def enter(self, character):
        pass

    def update(self, character):
        pass

    def exit(self, character):
        pass


class UpgradingToDiscoverer:
    def enter(self, character):
        character.entityManager.worldManager.messageDispatcher.dispatchMessage \
            (character, character, Enumerations.message_type.isUpgradedDiscoverer, 1, None)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class Discover:
    def enter(self, character):
        pass

    def update(self, character):
        # remove fog
        if character.pos in character.entityManager.worldManager.graph.fogNodes:
            character.entityManager.worldManager.graph.fogNodes.remove(character.pos)
        for neighbour in character.entityManager.worldManager.graph.neighbours(character.pos):
            if neighbour in character.entityManager.worldManager.graph.fogNodes:
                character.entityManager.worldManager.graph.fogNodes.remove(neighbour)

        if character.variables["nextFogNode"] is None:
            # find next fogNode
            # TODO: if another discoverer already has that node as destination, search again
            # TODO: can be optimized a lot by adding lists for occupied, browsing through fogNodes instead of graph etc
            character.variables["nextFogNode"] = Algorithms.findNearestFogNode\
                (character.entityManager.worldManager.graph, character.pos)
            if character.variables["nextFogNode"] is None:
                character.stateMachine.changeState(States.idle)
            else:
                path = Algorithms.findPathToNode\
                    (character.entityManager.worldManager.graph, character.pos, character.variables["nextFogNode"])
                character.route = Algorithms.getRoute(character.pos, character.variables["nextFogNode"], path)

        else:
            # get movin' to tha node
            if len(character.route) <= 0:
                character.variables["nextFogNode"] = None
            else:
                character.move(character.route[0], character.entityManager.worldManager.graph)
                character.route.pop(0)
                if len(character.route) <= 0:
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