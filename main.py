import pygame
import Parser
import Entity
import EntityManager
import WorldManager
import Graph
import StateMachine
import time


pygame.init()
screen = pygame.display.set_mode((1080, 1080))
pygame.display.set_caption("Strategiskt AI")
parser = Parser.Parser()
worldManager = WorldManager.WorldManager(EntityManager.EntityManager(), Graph.Graph())

worldManager.entityManager.worldManager = worldManager
mapName = "Lab3Map.txt"
worldManager.graph.loadToGraph(mapName)
worldManager.graph.setFog()
worldManager.graph.setStartPositions((75, 96))

# create entities
entityAmount = 50
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
for tree in range(700):
    worldManager.addNewTree()


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
