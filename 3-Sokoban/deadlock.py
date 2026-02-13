"""Deadlock detection for Sokoban states."""

from collections import deque
from puzzle import DIRECTIONS, move


def precompute_dead_squares(puzzle):
    """Compute squares where a single box would be permanently stuck.
    
    A square is dead if a box placed there (alone) could never reach any goal.
    We find this by doing reverse BFS from each goal: a box can be "pulled"
    from a square if the opposite side is free. Any square not reachable 
    from any goal by reverse-pull is dead.
    """
    alive = set()

    for goal in puzzle.goals:
        # BFS: which squares can a box reach this goal from (reverse pushes)?
        visited = set()
        queue = deque([goal])
        visited.add(goal)

        while queue:
            pos = queue.popleft()
            alive.add(pos)

            # Reverse push: box at `pos` was pushed in direction d to get here.
            # Before push: box was at pos - d, player was at pos - 2*d.
            # Both must be non-wall for the reverse step to be valid.
            for d in DIRECTIONS:
                dr, dc = DIRECTIONS[d]
                box_from = (pos[0] - dr, pos[1] - dc)
                player_was = (pos[0] - 2*dr, pos[1] - 2*dc)

                if (box_from not in puzzle.walls and 
                    player_was not in puzzle.walls and
                    box_from not in visited):
                    visited.add(box_from)
                    queue.append(box_from)

    # Dead squares = all floor squares not in alive set
    dead = set()
    for r in range(puzzle.height):
        for c in range(puzzle.width):
            pos = (r, c)
            if pos not in puzzle.walls and pos not in alive:
                dead.add(pos)

    return frozenset(dead)


def is_simple_deadlock(state, dead_squares):
    """Check if any box is on a dead square."""
    for box in state.boxes:
        if box in dead_squares:
            return True
    return False


def is_freeze_deadlock(state, puzzle):
    """Check for freeze deadlocks: boxes stuck in mutual blockage.
    
    A box is frozen on an axis if both neighbors on that axis are walls or frozen boxes.
    If any frozen box is not on a goal, the state is dead.
    """
    frozen = {}  # pos -> True/False/None (None = being computed)

    def is_frozen(pos):
        if pos not in state.boxes:
            return False
        if pos in frozen:
            return frozen[pos] if frozen[pos] is not None else True  # cycle = frozen
        
        frozen[pos] = None  # mark as being computed

        # Check horizontal: blocked if both left and right are wall or frozen box
        left = (pos[0], pos[1] - 1)
        right = (pos[0], pos[1] + 1)
        h_blocked = ((left in puzzle.walls or (left in state.boxes and is_frozen(left))) and
                     (right in puzzle.walls or (right in state.boxes and is_frozen(right))))

        # Check vertical: blocked if both up and down are wall or frozen box
        up = (pos[0] - 1, pos[1])
        down = (pos[0] + 1, pos[1])
        v_blocked = ((up in puzzle.walls or (up in state.boxes and is_frozen(up))) and
                     (down in puzzle.walls or (down in state.boxes and is_frozen(down))))

        frozen[pos] = h_blocked or v_blocked
        return frozen[pos]

    for box in state.boxes:
        if is_frozen(box) and box not in puzzle.goals:
            return True

    return False
