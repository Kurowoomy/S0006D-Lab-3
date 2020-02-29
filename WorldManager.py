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
        self.messageDispatcher = MessageSystem.MessageDispatcher()
        self.states = States.States()

    def update(self):
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

    def handleMessage(self, telegram):
        if telegram.msg == Enumerations.message_type.stopUpgrading:
            for message in self.messageDispatcher.priorityQ:
                # find message for upgrading sender entity
                if message[1].sender is telegram.sender and \
                        message[1].msg == Enumerations.message_type.isUpgradedDiscoverer:
                    self.messageDispatcher.priorityQ.remove(message)

