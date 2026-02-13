"""Flask web server for Sokoban solver."""

import json
import time
from flask import Flask, render_template, request, jsonify
from puzzle import Puzzle, State
from solver import solve, expand_solution

app = Flask(__name__)

# Pre-designed puzzles
PUZZLES = {
    "Level 1 - Tutorial": {
        "description": "One box, one push. Just get the idea.",
        "difficulty": "★",
        "map": (
            "#####\n"
            "#@$.#\n"
            "#####"
        )
    },
    "Level 2 - Walk First": {
        "description": "One box — but you need to walk around it.",
        "difficulty": "★",
        "map": (
            "######\n"
            "#    #\n"
            "# @$ #\n"
            "#  . #\n"
            "######"
        )
    },
    "Level 3 - Twin Boxes": {
        "description": "Two boxes, two goals. Push order matters!",
        "difficulty": "★★",
        "map": (
            "######\n"
            "# .. #\n"
            "#    #\n"
            "# $$ #\n"
            "# @  #\n"
            "######"
        )
    },
    "Level 4 - Sasquatch": {
        "description": "Two boxes in an L-shaped room.",
        "difficulty": "★★",
        "map": (
            "#####\n"
            "#   ##\n"
            "# $  #\n"
            "## $ #\n"
            " #.@ #\n"
            " #.  #\n"
            " #####"
        )
    },
    "Level 5 - The Gauntlet": {
        "description": "Two boxes blocked by a wall. Think ahead!",
        "difficulty": "★★★",
        "map": (
            "######\n"
            "#  . #\n"
            "#  $ #\n"
            "# .#@#\n"
            "# $  #\n"
            "#    #\n"
            "######"
        )
    },
    "Level 6 - Microban Classic": {
        "description": "The famous Microban #1 puzzle.",
        "difficulty": "★★★",
        "map": (
            "####\n"
            "# .#\n"
            "#  ###\n"
            "#*@  #\n"
            "#  $ #\n"
            "#  ###\n"
            "####"
        )
    },
    "Level 7 - Detour": {
        "description": "Two boxes — the long way around.",
        "difficulty": "★★★★",
        "map": (
            "########\n"
            "#      #\n"
            "# @##  #\n"
            "# $  . #\n"
            "#   #  #\n"
            "# $  . #\n"
            "#      #\n"
            "########"
        )
    },
    "Level 8 - Three's a Crowd": {
        "description": "Three boxes through narrow passages.",
        "difficulty": "★★★★",
        "map": (
            "########\n"
            "#      #\n"
            "# @$   #\n"
            "## $# ##\n"
            " # $  #\n"
            " # .. #\n"
            " # .  #\n"
            " ######"
        )
    },
    "Level 9 - The Maze": {
        "description": "Three boxes in a maze. Good luck!",
        "difficulty": "★★★★★",
        "map": (
            "########\n"
            "#  . . #\n"
            "# .    #\n"
            "#  ## ##\n"
            "# $$ @#\n"
            "#  $  #\n"
            "#     #\n"
            "#######"
        )
    },
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/puzzles', methods=['GET'])
def get_puzzles():
    """Return list of available puzzles."""
    result = {}
    for name, data in PUZZLES.items():
        result[name] = {
            'description': data['description'],
            'difficulty': data['difficulty'],
            'map': data['map']
        }
    return jsonify(result)


@app.route('/api/solve', methods=['POST'])
def solve_puzzle():
    """Solve a submitted puzzle. Accepts JSON with 'map' field."""
    data = request.get_json()
    if not data or 'map' not in data:
        return jsonify({'error': 'Missing puzzle map'}), 400

    puzzle_text = data['map']

    try:
        puzzle, initial_state = Puzzle.from_string(puzzle_text)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    start_time = time.time()
    try:
        solution = solve(puzzle, initial_state, max_states=200000)
    except (MemoryError, RecursionError):
        return jsonify({
            'solved': False,
            'message': 'Puzzle too complex — try fewer boxes or a smaller grid',
            'time': round(time.time() - start_time, 3)
        })
    elapsed = time.time() - start_time

    # Safety timeout: if it took more than 10 seconds, warn but still return
    if solution is None:
        return jsonify({
            'solved': False,
            'message': 'No solution found (puzzle may be unsolvable or too complex)',
            'time': round(elapsed, 3)
        })

    # Expand into individual walk + push frames for the frontend
    frames = expand_solution(puzzle, solution)

    return jsonify({
        'solved': True,
        'pushes': len(solution) - 1,
        'frames': frames,
        'walls': [list(w) for w in puzzle.walls],
        'goals': [list(g) for g in puzzle.goals],
        'width': puzzle.width,
        'height': puzzle.height,
        'time': round(elapsed, 3)
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
