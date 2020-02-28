import pygame
import Parser
import Entity
import EntityManager
import WorldManager
import Graph
import StateMachine
import States


pygame.init()
screen = pygame.display.set_mode((1080, 1080))
pygame.display.set_caption("Strategiskt AI")
parser = Parser.Parser()
worldManager = WorldManager.WorldManager(EntityManager.EntityManager(), Graph.Graph())

worldManager.entityManager.worldManager = worldManager
mapName = "Lab3Map.txt"
worldManager.graph.loadToGraph(mapName)
worldManager.graph.setFog()
worldManager.graph.setStartPositions((38, 58))

# create entities
entityAmount = 50
startPosIndex = 0
for entity in range(entityAmount):
    if startPosIndex >= 9:
        startPosIndex = 0
    newEntity = Entity.Entity("worker", worldManager.graph.startNodes[startPosIndex],
                              worldManager.entityManager)
    stateMachine = StateMachine.StateMachine(worldManager.states.lookForTree, newEntity)
    newEntity.stateMachine = stateMachine
    worldManager.entityManager.entities.append(newEntity)
    startPosIndex += 1

# create world
for tree in range(5):
    worldManager.addNewTree()


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # update logic--------------------
    worldManager.messageDispatcher.dispatchDelayedMessages()
    worldManager.update()

    # drawing-------------------------
    screen.fill((255, 255, 255))
    parser.drawMap(mapName, screen)
    parser.drawObjects(worldManager, screen)
    # parser.drawFog(worldManager.graph.fogNodes, screen)
    parser.drawEntities(worldManager.entityManager.entities, screen)

    # draw path

    pygame.display.update()
