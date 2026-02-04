"""
Motion planning on a rectangular grid using A* search
"""

from random import random
from random import seed
from queue import PriorityQueue
from copy import deepcopy


class State(object):

    def __init__(self, start_position, goal_position, start_grid):
        self.position = start_position
        self.goal = goal_position
        self.grid = start_grid
        self.total_moves = 0

    def manhattan_distance(self):
        """Calculate Manhattan distance from current position to goal"""
        return abs(self.position[0] - self.goal[0]) + abs(self.position[1] - self.goal[1])

    def __lt__(self, other):
        """Comparison for PriorityQueue tie-breaking"""
        return self.position < other.position


def create_grid():

    """
    Create and return a randomized grid

    0's in the grid indcate free squares
    1's indicate obstacles

    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    ARE YOU MODIFYING THIS ROUTINE?
    IF SO, STOP IT.
    """

    # Start with a num_rows by num_cols grid of all zeros
    grid = [[0 for c in range(num_cols)] for r in range(num_rows)]

    # Put ones around the boundary
    grid[0] = [1 for c in range(num_cols)]
    grid[num_rows - 1] = [1 for c in range(num_cols)]

    for r in range(num_rows):
        grid[r][0] = 1
        grid[r][num_cols - 1] = 1

    # Sprinkle in obstacles randomly
    for r in range(1, num_rows - 1):
        for c in range(2, num_cols - 2):
            if random() < obstacle_prob:
                grid[r][c] = 1;

    # Make sure the goal and start spaces are clear
    grid[1][1] = 0
    grid[num_rows - 2][num_cols - 2] = 0

    return grid


def print_grid(grid):

    """
    Print a grid, putting spaces in place of zeros for readability

    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    ARE YOU MODIFYING THIS ROUTINE?
    IF SO, STOP IT.
    """

    for r in range(num_rows):
        for c in range(num_cols):
            if grid[r][c] == 0:
                print(' ', end='')
            else:
                print(grid[r][c], end='')
        print('')

    print('')

    return 


def main():
    """
    Use A* search to find a path from the upper left to the lower right
    of the puzzle grid

    Complete this method to implement the search
    At the end, print the solution state
    
    Each State object has a copy of the grid
    
    When you make a move by generating a new State, put a * on its grid
    to show the solution path
    """

  
    # Setup the randomized grid
    grid = create_grid()
    print_grid(grid)

    # Initialize the starting state and priority queue
    start_position = (1, 1)
    goal_position = (num_rows - 2, num_cols - 2)
    start_state = State(start_position, goal_position, grid)
    start_state.grid[1][1] = '*'

    # A* priority: implement the Manhattan distance in the State class
    priority = start_state.total_moves + start_state.manhattan_distance()

    queue = PriorityQueue()

    # Insert as a tuple
    # The queue orders elements by the first tuple value
    # A call to queue.get() returns the tuple with the minimum first value
    queue.put((priority, start_state))

    # Track visited positions
    visited = {}

    # Possible moves: up, down, left, right
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while not queue.empty():
        # Get state with lowest priority (f = g + h)
        priority, current_state = queue.get()

        # Check if we've reached the goal
        if current_state.position == goal_position:
            print("Solution found!")
            print_grid(current_state.grid)
            return

        # Skip if we've already visited this position with equal or lower cost
        if current_state.position in visited:
            if visited[current_state.position] <= current_state.total_moves:
                continue

        # Mark position as visited with current cost
        visited[current_state.position] = current_state.total_moves

        # Generate successor states
        for move in moves:
            new_row = current_state.position[0] + move[0]
            new_col = current_state.position[1] + move[1]
            new_position = (new_row, new_col)

            # Check if the new position is free (not an obstacle or wall)
            if current_state.grid[new_row][new_col] != 1 and current_state.grid[new_row][new_col] != '*':
                # Create new state with a copy of the grid
                new_grid = deepcopy(current_state.grid)
                new_grid[new_row][new_col] = '*'

                new_state = State(new_position, goal_position, new_grid)
                new_state.total_moves = current_state.total_moves + 1

                # Calculate A* priority: f = g + h
                new_priority = new_state.total_moves + new_state.manhattan_distance()
                queue.put((new_priority, new_state))

    # No path found
    print("No path exists!")
    print_grid(grid)


if __name__ == '__main__':

    seed(0)

    #--- Easy mode

    # Global variables
    # Saves us the trouble of continually passing them as parameters 
    num_rows = 8
    num_cols = 16
    obstacle_prob = .20

    for trial in range(5):
        print('\n\n-----Easy trial ' + str(trial + 1) + '-----')
        main()

    #--- Uncomment the following sets of trials when you're ready

    #--- Hard mode
    num_rows = 15
    num_cols = 30
    obstacle_prob = .30

    for trial in range(5):
        print('\n\n-----Harder trial ' + str(trial + 1) + '-----')
        main()

    #--- INSANE mode
    num_rows = 20
    num_cols = 60
    obstacle_prob = .35

    for trial in range(5):
        print('\n\n-----INSANE trial ' + str(trial + 1) + '-----')
        main()