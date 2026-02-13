"""A* search solver for Sokoban puzzles."""

import heapq
from collections import deque
from puzzle import State, DIRECTIONS, move
from heuristic import precompute_goal_distances, hungarian_heuristic
from deadlock import precompute_dead_squares, is_simple_deadlock, is_freeze_deadlock


def find_reachable(player, walls, boxes):
    """BFS to find all squares reachable by the player (without pushing boxes)."""
    obstacles = walls | boxes
    visited = set()
    queue = deque([player])
    visited.add(player)

    while queue:
        pos = queue.popleft()
        for d in DIRECTIONS:
            dr, dc = DIRECTIONS[d]
            npos = (pos[0] + dr, pos[1] + dc)
            if npos not in obstacles and npos not in visited:
                visited.add(npos)
                queue.append(npos)

    return visited


def find_path(start, end, walls, boxes):
    """BFS to find shortest walking path from start to end, avoiding walls and boxes.
    
    Returns list of (row, col) positions from start to end inclusive.
    """
    if start == end:
        return [start]
    obstacles = walls | boxes
    visited = {start}
    parent = {}
    queue = deque([start])

    while queue:
        pos = queue.popleft()
        for d in DIRECTIONS:
            dr, dc = DIRECTIONS[d]
            npos = (pos[0] + dr, pos[1] + dc)
            if npos not in obstacles and npos not in visited:
                visited.add(npos)
                parent[npos] = pos
                if npos == end:
                    # Reconstruct path
                    path = []
                    cur = npos
                    while cur is not None:
                        path.append(cur)
                        cur = parent.get(cur)
                    path.reverse()
                    return path
                queue.append(npos)

    return [start]  # fallback (shouldn't happen if puzzle is valid)


def expand_solution(puzzle, push_solution):
    """Expand push-only solution into individual walk + push frames.
    
    Each frame is a dict with:
        player: [r, c]
        boxes: [[r, c], ...]
        label: description string
        is_push: bool
    """
    frames = []

    # Frame 0: initial state
    init_state = push_solution[0][0]
    frames.append({
        'player': list(init_state.player),
        'boxes': [list(b) for b in init_state.boxes],
        'label': 'Initial state',
        'is_push': False
    })

    cur_player = init_state.player
    cur_boxes = init_state.boxes  # frozenset

    dir_names = {'U': '⬆ Up', 'D': '⬇ Down', 'L': '⬅ Left', 'R': '➡ Right'}
    total_pushes = len(push_solution) - 1

    for i in range(1, len(push_solution)):
        state, direction, box_from, box_to = push_solution[i]

        # Player needs to walk to the square behind the box before pushing
        dr, dc = DIRECTIONS[direction]
        behind_box = (box_from[0] - dr, box_from[1] - dc)

        # Find walking path from current position to behind the box
        walk_path = find_path(cur_player, behind_box, puzzle.walls, cur_boxes)

        # Add one frame per walking step (skip index 0, that's current position)
        for w in range(1, len(walk_path)):
            frames.append({
                'player': list(walk_path[w]),
                'boxes': [list(b) for b in cur_boxes],
                'label': 'Walking…',
                'is_push': False
            })

        # Now the push: player moves to where box was, box moves forward
        new_boxes = (cur_boxes - {box_from}) | {box_to}
        frames.append({
            'player': list(box_from),
            'boxes': [list(b) for b in new_boxes],
            'label': f'Push {i} of {total_pushes} — {dir_names[direction]}',
            'is_push': True
        })

        cur_player = box_from
        cur_boxes = new_boxes

    return frames


def normalize_player(player, walls, boxes):
    """Normalize player position to canonical form (top-left of reachable area).
    
    Two states with the same box positions where the player can reach the same
    squares are equivalent. We normalize to reduce the state space.
    """
    reachable = find_reachable(player, walls, boxes)
    return min(reachable)  # top-left: min by (row, col)


def get_successors(state, puzzle):
    """Generate all valid successor states by pushing boxes.
    
    For each box, for each direction, check:
    1. The square behind the box (opposite to push direction) is reachable by player
    2. The square in front of the box (push direction) is free (no wall, no box)
    
    Returns list of (new_state, direction, box_from, box_to, move_cost).
    move_cost = number of player walk steps to get behind box + 1 for the push.
    """
    # BFS to find reachable squares AND distances from player
    obstacles = puzzle.walls | state.boxes
    dist = {state.player: 0}
    queue = deque([state.player])
    while queue:
        pos = queue.popleft()
        for d in DIRECTIONS:
            dr, dc = DIRECTIONS[d]
            npos = (pos[0] + dr, pos[1] + dc)
            if npos not in obstacles and npos not in dist:
                dist[npos] = dist[pos] + 1
                queue.append(npos)

    successors = []
    for box in state.boxes:
        for d_name, (dr, dc) in DIRECTIONS.items():
            player_pos = (box[0] - dr, box[1] - dc)
            new_box_pos = (box[0] + dr, box[1] + dc)

            if (player_pos in dist and
                new_box_pos not in puzzle.walls and
                new_box_pos not in state.boxes):

                new_boxes = (state.boxes - {box}) | {new_box_pos}
                new_state = State(box, new_boxes)
                move_cost = dist[player_pos] + 1  # walk steps + 1 push
                successors.append((new_state, d_name, box, new_box_pos, move_cost))

    return successors


def solve(puzzle, initial_state, max_states=200000):
    """Solve a Sokoban puzzle using A* search.
    
    Returns:
        list of (state, push_direction, box_from, box_to) or None if unsolvable.
        First element is (initial_state, None, None, None).
    """
    # Precomputation
    dead_squares = precompute_dead_squares(puzzle)
    goal_distances = precompute_goal_distances(puzzle)

    # Check initial state
    if initial_state.is_solved(puzzle):
        return [(initial_state, None, None, None)]

    if is_simple_deadlock(initial_state, dead_squares):
        return None

    # A* search
    # State key: (normalized_player, boxes) for deduplication
    def state_key(state):
        norm_player = normalize_player(state.player, puzzle.walls, state.boxes)
        return (norm_player, state.boxes)

    # Use came_from dict instead of storing full paths
    init_key = state_key(initial_state)
    h0 = hungarian_heuristic(initial_state, puzzle, goal_distances)
    counter = 0
    open_set = [(h0, counter, initial_state)]
    g_scores = {init_key: 0}
    came_from = {init_key: None}  # key -> (parent_key, parent_state, direction, box_from, box_to)
    state_map = {init_key: initial_state}
    explored = 0

    while open_set and explored < max_states:
        f, _, current = heapq.heappop(open_set)
        explored += 1

        key = state_key(current)
        current_g = g_scores.get(key, float('inf'))

        if current.is_solved(puzzle):
            # Reconstruct path
            path = []
            k = key
            while k is not None:
                info = came_from[k]
                s = state_map[k]
                if info is None:
                    path.append((s, None, None, None))
                else:
                    _, _, d, bf, bt = info
                    path.append((s, d, bf, bt))
                k = info[0] if info else None
            path.reverse()
            return path

        for new_state, direction, box_from, box_to, move_cost in get_successors(current, puzzle):
            # Deadlock pruning
            if is_simple_deadlock(new_state, dead_squares):
                continue
            if is_freeze_deadlock(new_state, puzzle):
                continue

            new_g = current_g + move_cost
            new_key = state_key(new_state)

            if new_key not in g_scores or new_g < g_scores[new_key]:
                g_scores[new_key] = new_g
                came_from[new_key] = (key, current, direction, box_from, box_to)
                state_map[new_key] = new_state
                h = hungarian_heuristic(new_state, puzzle, goal_distances)
                f = new_g + h
                counter += 1
                heapq.heappush(open_set, (f, counter, new_state))

    return None  # No solution found
