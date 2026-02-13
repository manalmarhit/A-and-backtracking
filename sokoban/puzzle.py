"""Sokoban puzzle representation and loading."""

class Puzzle:
    """Represents a Sokoban puzzle (the static parts: walls, goals, dimensions)."""

    def __init__(self, walls, goals, width, height):
        self.walls = frozenset(walls)
        self.goals = frozenset(goals)
        self.width = width
        self.height = height

    @classmethod
    def from_string(cls, text):
        """Parse a puzzle from standard Sokoban text format.
        
        Returns (puzzle, initial_state) tuple.
        
        Characters:
            # = wall, $ = box, . = goal, @ = player
            * = box on goal, + = player on goal, space = floor
        """
        lines = text.strip().split('\n')
        walls = set()
        goals = set()
        boxes = set()
        player = None
        height = len(lines)
        width = max(len(line) for line in lines)

        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == '#':
                    walls.add((r, c))
                elif ch == '$':
                    boxes.add((r, c))
                elif ch == '.':
                    goals.add((r, c))
                elif ch == '@':
                    player = (r, c)
                elif ch == '*':  # box on goal
                    boxes.add((r, c))
                    goals.add((r, c))
                elif ch == '+':  # player on goal
                    player = (r, c)
                    goals.add((r, c))

        if player is None:
            raise ValueError("No player (@) found in puzzle")
        if len(boxes) == 0:
            raise ValueError("No boxes ($) found in puzzle")
        if len(boxes) != len(goals):
            raise ValueError(f"Mismatch: {len(boxes)} boxes but {len(goals)} goals")

        puzzle = cls(walls, goals, width, height)
        state = State(player, frozenset(boxes))
        return puzzle, state

    def is_free(self, pos):
        """Check if a position is not a wall."""
        return pos not in self.walls

    def to_string(self, state):
        """Render the puzzle + state as a string."""
        lines = []
        for r in range(self.height):
            row = []
            for c in range(self.width):
                pos = (r, c)
                if pos in self.walls:
                    row.append('#')
                elif pos == state.player and pos in self.goals:
                    row.append('+')
                elif pos == state.player:
                    row.append('@')
                elif pos in state.boxes and pos in self.goals:
                    row.append('*')
                elif pos in state.boxes:
                    row.append('$')
                elif pos in self.goals:
                    row.append('.')
                else:
                    row.append(' ')
            lines.append(''.join(row))
        return '\n'.join(lines)


class State:
    """A game state: player position + box positions."""

    def __init__(self, player, boxes):
        self.player = player          # (row, col)
        self.boxes = frozenset(boxes)  # frozenset of (row, col)

    def __eq__(self, other):
        return self.player == other.player and self.boxes == other.boxes

    def __hash__(self):
        return hash((self.player, self.boxes))

    def is_solved(self, puzzle):
        """Check if all boxes are on goals."""
        return self.boxes == puzzle.goals


# Direction helpers
DIRECTIONS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1),
}

def move(pos, direction):
    """Return new position after moving in a direction."""
    dr, dc = DIRECTIONS[direction]
    return (pos[0] + dr, pos[1] + dc)
