import Enumerations


class States:
    def __init__(self):
        States.lookForTree = LookForTree()
        States.upgradingToDiscoverer = UpgradingToDiscoverer()
        States.discover = Discover()


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
            (character, character, Enumerations.message_type.isUpgradedDiscoverer, 60, None)

    def update(self, character):
        pass

    def exit(self, character):
        pass


class Discover:
    def enter(self, character):
        print("upgraded to discoverer")

    def update(self, character):
        pass

    def exit(self, character):
        pass
