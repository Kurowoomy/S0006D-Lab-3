

class EntityManager:

    def __init__(self):
        self.entities = []
        self.workers = []
        self.discoverers = []
        self.isUpgrading = []
        self.worldManager = None
        self.builders = []
        self.kilnManagers = []

    def update(self):
        for entity in self.entities:
            entity.update()
