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
worldManager = WorldManager.WorldManager(EntityManager.EntityManager(), Graph.Graph())

worldManager.entityManager.worldManager = worldManager
mapName = variables["mainVariables"]["mapName"]
worldManager.graph.loadToGraph(mapName)
worldManager.graph.setFog()
worldManager.graph.setStartPositions(tuple(variables["mainVariables"]["startPosition"]))

# create entities
entityAmount = variables["mainVariables"]["entityAmount"]
startPosIndex = 0
ID = 0
for entity in range(entityAmount):
    if startPosIndex >= 9:
        startPosIndex = 0
    newEntity = Entity.Entity("worker", worldManager.graph.startNodes[startPosIndex],
                              worldManager.entityManager, ID)
    newEntity.variables["item"] = None
    stateMachine = StateMachine.StateMachine(worldManager.states.wandering, newEntity)
    newEntity.stateMachine = stateMachine
    worldManager.entityManager.entities.append(newEntity)
    worldManager.entityManager.workers.append(newEntity)
    startPosIndex += 1
    ID += 1

# create world
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
    start = time.perf_counter()
    worldManager.update()
    # TODO: create a pathFinding scripts/class to keep in worldManager and execute it evenly so it won't lag, and then
    # TODO: return path from worldManager.pathFinding to owner of path when it's done
    if time.perf_counter() - start >= 1:
        print("Plz don't take more than 1 second DD: I'll cry")
    if worldManager.charcoal >= worldManager.charcoalGoal and not goalIsReached:
        goalIsReached = True
        print("Making", worldManager.charcoal, "charcoal took", time.perf_counter() - startGame, "seconds")

    start = time.perf_counter()
    worldManager.doPathFinding()
    if time.perf_counter() - start >= 1:
        print("Path finder still takes too much time (1 second or more)")

    # drawing-------------------------
    screen.fill((255, 255, 255))
    parser.drawMap(mapName, screen)
    parser.drawObjects(worldManager, screen)
    parser.drawFog(worldManager.graph.fogNodes, screen)
    parser.drawEntities(worldManager, screen)

    # draw path

    pygame.display.update()
