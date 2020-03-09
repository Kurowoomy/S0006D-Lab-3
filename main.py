import pygame
import Parser
import Entity
import EntityManager
import WorldManager
import Graph
import StateMachine
import time
import json

f = open("variables.json")
variables = json.load(f)

pygame.init()
screen = pygame.display.set_mode((1080, 1080))
pygame.display.set_caption("Strategiskt AI")
parser = Parser.Parser()
worldManager = WorldManager.WorldManager(EntityManager.EntityManager(), Graph.Graph(),
                                         variables["worldManagerVariables"], variables["moveVariables"])

worldManager.entityManager.worldManager = worldManager
mapName = variables["mainVariables"]["mapName"]
worldManager.graph.loadToGraph(mapName)
worldManager.graph.setFog()
worldManager.graph.setStartPositions(tuple(variables["mainVariables"]["startPosition"]))
worldManager.graph.setUnreachablePositions(variables["mainVariables"]["unreachableNodes"])

# create entities------------
entityAmount = variables["mainVariables"]["entityAmount"]
# graph has list of positions from 0 to 9 to represent the pos relative to the start pos in variables.json
startPosIndex = 0  # increments after each entity creation up to 8. Start positions create a square of 3x3.
ID = 0
for entity in range(entityAmount):
    if startPosIndex >= 9:
        startPosIndex = 0
    newEntity = Entity.Entity("worker", worldManager.graph.startNodes[startPosIndex],
                              worldManager.entityManager, ID, variables["entityVariables"])
    newEntity.variables["item"] = None
    stateMachine = StateMachine.StateMachine(worldManager.states.wandering, newEntity)
    newEntity.stateMachine = stateMachine
    worldManager.entityManager.entities.append(newEntity)
    worldManager.entityManager.workers.append(newEntity)
    startPosIndex += 1
    ID += 1

# create world----------------
for tree in range(variables["mainVariables"]["treeAmount"]):
    worldManager.addNewTree()

startGame = time.perf_counter()
goalIsReached = False
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # update logic--------------------
    worldManager.messageDispatcher.dispatchDelayedMessages()
    worldManager.update()
    if worldManager.charcoal >= worldManager.charcoalGoal and not goalIsReached:
        goalIsReached = True
        print("Making", worldManager.charcoal, "charcoal took", time.perf_counter() - startGame, "seconds")

    worldManager.doPathFinding()

    # drawing-------------------------
    screen.fill((255, 255, 255))
    parser.drawMap(mapName, screen)
    parser.drawObjects(worldManager, screen)
    parser.drawFog(worldManager.graph.fogNodes, screen)
    parser.drawEntities(worldManager, screen)

    pygame.display.update()
