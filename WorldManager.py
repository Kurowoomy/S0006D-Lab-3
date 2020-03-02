import random
import Objects
import MessageSystem
import States
import Enumerations


class WorldManager:
    def __init__(self, entityManager, graph):
        self.entityManager = entityManager
        self.graph = graph
        self.trees = {}
        self.buildings = {}
        self.messageDispatcher = MessageSystem.MessageDispatcher()
        self.states = States.States()
        self.needDiscoverers = True
        self.needBuilders = True
        self.needKilnManager = True
        self.gatheredTreesAvailable = 0
        self.needKiln = True
        self.AStarHasOccurred = False
        self.charcoal = 0

    def update(self):
        if self.gatheredTreesAvailable >= 4 and self.needBuilders:
            for entity in self.entityManager.workers:
                if not entity.isWorking and entity not in self.entityManager.isUpgrading:
                    entity.stateMachine.changeState(self.states.upgradingToBuilder)
                    self.needBuilders = False
                    break
        if self.gatheredTreesAvailable >= 4 and self.needKilnManager:
            for entity in self.entityManager.workers:
                if not entity.isWorking and entity not in self.entityManager.isUpgrading:
                    entity.stateMachine.changeState(self.states.upgradingToKilnManager)
                    self.needKilnManager = False
                    break

        self.AStarHasOccurred = False
        self.entityManager.update()

    def addNewTree(self):
        treeIndex = random.randrange(0, len(self.graph.treeNodes))
        foundFreeNode = False
        while not foundFreeNode:
            foundFreeNode = True
            for tree in self.trees:  # TODO: are dictionaries iterable?
                if self.graph.treeNodes[treeIndex] == self.trees[tree].pos:
                    treeIndex = random.randrange(0, len(self.graph.treeNodes))
                    foundFreeNode = False
                    break

        tree = Objects.Tree(self.graph.treeNodes[treeIndex])
        self.trees[self.graph.treeNodes[treeIndex]] = tree

        return tree

    def handleMessage(self, telegram):
        if telegram.msg == Enumerations.message_type.stopUpgrading:
            for message in self.messageDispatcher.priorityQ:
                # find message for upgrading sender entity
                if message[1].sender is telegram.sender and \
                        message[1].msg == Enumerations.message_type.isUpgradedDiscoverer:
                    self.messageDispatcher.priorityQ.remove(message)

    def removeAllMessagesOf(self, messageType, entity):
        for message in self.messageDispatcher.priorityQ:
            if message[1].reciever is entity and message[1].msg == messageType:
                self.messageDispatcher.priorityQ.remove(message)

