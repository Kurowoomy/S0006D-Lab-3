import collections
import heapq
import random


def findNearestFogNodeBFS(graph, start):
    queue = collections.deque()
    queue.append(start)
    path = {tuple(start): None}

    maxLoops = 3
    maxCost = maxLoops * 10 + maxLoops * 14
    currentNode = start
    while heuristic(currentNode, start) <= maxCost:
        currentNode = queue.popleft()

        if currentNode in graph.fogNodes and currentNode not in graph.occupiedNodes:
            return currentNode, path

        for neighbour in graph.neighbours(currentNode):
            if tuple(neighbour) not in path:
                queue.append(neighbour)
                path[tuple(neighbour)] = currentNode

    return findNearestRandomFogNode(graph), path


def findNearestRandomFogNode(graph):
    if len(graph.fogNodes) <= len(graph.occupiedNodes):
        return None
    notTestedNodes = graph.fogNodes.copy()
    currentNode = random.choice(notTestedNodes)
    notTestedNodes.remove(currentNode)
    while currentNode in graph.occupiedNodes:
        currentNode = random.choice(notTestedNodes)
        notTestedNodes.remove(currentNode)
    return currentNode


def findPathToNode(graph, start, goal):
    priorityQ = []
    heapq.heappush(priorityQ, (0, tuple(start)))
    path = {tuple(start): None}
    costSoFar = {tuple(start): 0}

    while len(priorityQ) != 0:
        currentNode = heapq.heappop(priorityQ)[1]

        if currentNode == tuple(goal):
            break

        for neighbour in graph.neighbours(currentNode):
            newCost = costSoFar[currentNode] + tileDependentHeuristic(graph, neighbour, currentNode)
            if (tuple(neighbour) not in costSoFar) or (newCost < costSoFar[tuple(neighbour)]):
                costSoFar[tuple(neighbour)] = newCost
                priority = newCost + heuristic(goal, neighbour)
                path[tuple(neighbour)] = currentNode
                heapq.heappush(priorityQ, (priority, tuple(neighbour)))

    return path


def findPathAvoidFog(graph, start, goal):
    priorityQ = []
    heapq.heappush(priorityQ, (0, tuple(start)))
    path = {tuple(start): None}
    costSoFar = {tuple(start): 0}

    while len(priorityQ) != 0:
        currentNode = heapq.heappop(priorityQ)[1]

        if currentNode == tuple(goal):
            break

        for neighbour in graph.neighboursExceptFog(currentNode):
            if neighbour not in graph.fogNodes:
                newCost = costSoFar[currentNode] + tileDependentHeuristic(graph, neighbour, currentNode)
                if (tuple(neighbour) not in costSoFar) or (newCost < costSoFar[tuple(neighbour)]):
                    costSoFar[tuple(neighbour)] = newCost
                    priority = newCost + heuristic(goal, neighbour)
                    path[tuple(neighbour)] = currentNode
                    heapq.heappush(priorityQ, (priority, tuple(neighbour)))
            else:  # if neighbour is in a fogNode, plz don't choose this node I beg you :((
                newCost = costSoFar[currentNode] + 10000000000000000000000000000000000
                if (tuple(neighbour) not in costSoFar) or (newCost < costSoFar[tuple(neighbour)]):
                    costSoFar[tuple(neighbour)] = newCost
                    priority = newCost + heuristic(goal, neighbour)
                    path[tuple(neighbour)] = currentNode
                    heapq.heappush(priorityQ, (priority, tuple(neighbour)))

    return path


def findPathAndDistance(graph, start, goal):
    priorityQ = []
    heapq.heappush(priorityQ, (0, tuple(start)))
    path = {tuple(start): None}
    costSoFar = {tuple(start): 0}

    while len(priorityQ) != 0:
        currentNode = heapq.heappop(priorityQ)[1]

        if currentNode == tuple(goal):
            break

        for neighbour in graph.neighbours(currentNode):
            newCost = costSoFar[currentNode] + tileDependentHeuristic(graph, neighbour, currentNode)
            if (tuple(neighbour) not in costSoFar) or (newCost < costSoFar[tuple(neighbour)]):
                costSoFar[tuple(neighbour)] = newCost
                priority = newCost + heuristic(goal, neighbour)
                path[tuple(neighbour)] = currentNode
                heapq.heappush(priorityQ, (priority, tuple(neighbour)))

    return path, costSoFar[tuple(goal)]


def heuristic(goal, next):
    remaining = abs(abs(goal[0] - next[0]) - abs(goal[1] - next[1]))
    if abs(goal[0] - next[0]) < abs(goal[1] - next[1]):
        return 14 * abs(goal[0] - next[0]) + remaining * 10
    else:
        return 14 * abs(goal[1] - next[1]) + remaining * 10


def tileDependentHeuristic(graph, next, current):
    if current in graph.groundNodes and next in graph.groundNodes:
        diagonalCost = 7
        straightCost = 5
    elif (current in graph.groundNodes and next in graph.swampNodes) or \
            (current in graph.swampNodes and next in graph.groundNodes):
        diagonalCost = 21
        straightCost = 15
    elif current in graph.swampNodes and next in graph.swampNodes:
        diagonalCost = 28
        straightCost = 20

    remaining = abs(abs(next[0] - current[0]) - abs(next[1] - current[1]))
    if abs(next[0] - current[0]) < abs(next[1] - current[1]):
        return diagonalCost * abs(next[0] - current[0]) + remaining * straightCost
    else:
        return diagonalCost * abs(next[1] - current[1]) + remaining * straightCost


def getRoute(start, goal, path):
    if len(path) <= 0:
        return [(0, 0)]

    node = tuple(goal)
    route = [node]
    while node != tuple(start):
        if node is None:
            print("node: Nonetype object :((")
        if path[node] is None:
            print("path[", node, "]: Nonetype object :((")  # TODO: fixa denna bugg
        node = tuple(path[node])
        route.append(node)

    route.reverse()
    route.pop(0)
    return route


def getBFSRoute(start, goal, graph, previousPath):
    queue = collections.deque()
    queue.append(start)
    path = previousPath

    while len(queue) != 0:
        currentNode = queue.popleft()  # treat queue as a stack by using popleft

        if currentNode == goal:
            break

        for neighbour in graph.neighbours(currentNode):
            if tuple(neighbour) not in path:
                queue.append(neighbour)
                path[tuple(neighbour)] = currentNode

    return getRoute(start, goal, path)
