

class EntityManager:

    def __init__(self):
        self.entities = []
        self.workers = []
        self.worldManager = None

    def update(self):
        for entity in self.entities:
            entity.update()
