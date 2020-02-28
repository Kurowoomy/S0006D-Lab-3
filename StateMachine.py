

class StateMachine:
    def __init__(self, currentState, entity):
        self.owner = entity
        self.currentState = currentState

    def update(self):
        self.currentState.update(self.owner)

    def changeState(self, newState):
        self.currentState.exit(self.owner)
        self.currentState = newState
        self.currentState.enter(self.owner)
