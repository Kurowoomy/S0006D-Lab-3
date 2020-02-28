import random
import Objects
import MessageSystem
import States


class WorldManager:
    def __init__(self, entityManager, graph):
        self.entityManager = entityManager
        self.graph = graph
        self.trees = []
        self.messageDispatcher = MessageSystem.MessageDispatcher()
        self.states = States.States()

    def update(self):
        self.entityManager.update()

    def addNewTree(self):
        treeIndex = random.randrange(0, len(self.graph.treeNodes))
        foundFreeNode = False
        while not foundFreeNode:
            foundFreeNode = True
            for tree in self.trees:
                if self.graph.treeNodes[treeIndex] == tree.pos:
                    treeIndex = random.randrange(0, len(self.graph.treeNodes))
                    foundFreeNode = False
                    break

        tree = Objects.Tree(self.graph.treeNodes[treeIndex])
        self.trees.append(tree)
