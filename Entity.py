import States
import Enumerations


class Entity:
    def __init__(self, occupation, pos, entityManager):
        self.occupation = occupation
        self.pos = pos
        self.entityManager = entityManager
        self.stateMachine = None

    def update(self):
        # upgrade to discoverer if needed
        if self.occupation == "worker":

            if self.stateMachine.currentState is States.States.lookForTree and self.noOneIsDiscoveringAt(self.pos):

                neighbours = self.entityManager.worldManager.graph.neighbours(self.pos)
                for neighbour in neighbours:

                    if neighbour in self.entityManager.worldManager.graph.fogNodes:
                        self.stateMachine.changeState(States.States.upgradingToDiscoverer)

        self.stateMachine.update()

    def noOneIsDiscoveringAt(self, node):
        for entity in self.entityManager.entities:
            if entity.pos == node:
                if entity.occupation == "discoverer" or \
                        entity.stateMachine.currentState is States.States.upgradingToDiscoverer:
                    return False
        return True

    def handleMessage(self, telegram):
        if telegram.msg == Enumerations.message_type.isUpgradedDiscoverer:
            self.occupation = "discoverer"
            self.stateMachine.changeState(States.States.discover)
