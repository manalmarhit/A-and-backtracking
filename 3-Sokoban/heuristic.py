"""Heuristic functions for Sokoban A* search."""

from collections import deque
from puzzle import DIRECTIONS


def precompute_goal_distances(puzzle):
    """BFS from each goal to compute shortest distance to every reachable square.
    
    Ignores boxes (only walls block). Returns dict: goal_pos -> {pos: distance}.
    """
    distances = {}

    for goal in puzzle.goals:
        dist = {goal: 0}
        queue = deque([goal])

        while queue:
            pos = queue.popleft()
            for d in DIRECTIONS:
                dr, dc = DIRECTIONS[d]
                npos = (pos[0] + dr, pos[1] + dc)
                if npos not in puzzle.walls and npos not in dist:
                    dist[npos] = dist[pos] + 1
                    queue.append(npos)

        distances[goal] = dist

    return distances


def hungarian_heuristic(state, puzzle, goal_distances):
    """Compute minimum cost matching between boxes and goals using Hungarian algorithm.
    
    Cost matrix: distance from each box to each goal (precomputed BFS distances).
    Returns the minimum total cost assignment.
    """
    boxes = list(state.boxes)
    goals = list(puzzle.goals)
    n = len(boxes)

    if n == 0:
        return 0

    # Build cost matrix
    cost = []
    for box in boxes:
        row = []
        for goal in goals:
            d = goal_distances[goal].get(box, 999999)  # unreachable = huge cost
            row.append(d)
        cost.append(row)

    # Hungarian algorithm (Kuhn-Munkres) for square cost matrix
    return _hungarian(cost, n)


def _hungarian(cost, n):
    """Hungarian algorithm for n x n cost matrix. Returns minimum total cost."""
    INF = float('inf')
    
    # u[i] = potential for worker i, v[j] = potential for job j
    u = [0] * (n + 1)
    v = [0] * (n + 1)
    # p[j] = worker assigned to job j (1-indexed, 0 = unassigned)
    p = [0] * (n + 1)
    # way[j] = previous job in augmenting path
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0  # virtual job
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1

            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        while j0:
            p[j0] = p[way[j0]]
            j0 = way[j0]

    return -v[0]


def manhattan_heuristic(state, puzzle):
    """Simple fallback: sum of Manhattan distances from each box to nearest goal."""
    total = 0
    for box in state.boxes:
        min_dist = min(abs(box[0] - g[0]) + abs(box[1] - g[1]) for g in puzzle.goals)
        total += min_dist
    return total
