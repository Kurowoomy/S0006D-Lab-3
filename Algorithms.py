import collections
import heapq


def findNearestFogNode(graph, start):
    queue = collections.deque()
    queue.append(start)
    path = {tuple(start): None}

    while len(queue) != 0:
        currentNode = queue.popleft()  # treat queue as a stack by using popleft

        if currentNode in graph.fogNodes:
            return currentNode

        for neighbour in graph.neighbours(currentNode):
            if tuple(neighbour) not in path:
                queue.append(neighbour)
                path[tuple(neighbour)] = currentNode

    return None


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
        return []

    node = tuple(goal)
    route = [node]
    while node != tuple(start):
        node = tuple(path[node])
        route.append(node)

    route.reverse()
    route.pop(0)
    return route
