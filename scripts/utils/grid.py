"""Grid utilities: BFS shortest path, grid rendering, coordinate helpers."""

from collections import deque
from typing import List, Optional, Tuple

# World encoding
EMPTY = 0
OBSTACLE = 1
START = 2
GOAL = 3

# Action definitions: (delta_row, delta_col)
ACTION_DELTAS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}

ACTION_LIST = ["up", "down", "left", "right"]


def bfs_shortest_path(
    world: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Optional[List[str]]:
    """Return the lexicographically first shortest action sequence via BFS, or None if unreachable."""
    rows = len(world)
    cols = len(world[0])

    if start == goal:
        return []

    visited = {start}
    # Each queue item: (current_pos, path_so_far)
    queue = deque([(start, [])])

    while queue:
        pos, path = queue.popleft()
        for action in ACTION_LIST:
            dr, dc = ACTION_DELTAS[action]
            nr, nc = pos[0] + dr, pos[1] + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if world[nr][nc] != OBSTACLE and (nr, nc) not in visited:
                    new_path = path + [action]
                    if (nr, nc) == goal:
                        return new_path
                    visited.add((nr, nc))
                    queue.append(((nr, nc), new_path))

    return None


def render_grid(world: List[List[int]]) -> str:
    """Render a world grid to a human-readable ASCII string."""
    symbols = {EMPTY: ".", OBSTACLE: "#", START: "S", GOAL: "G"}
    rows = []
    for row in world:
        rows.append(" ".join(symbols.get(cell, "?") for cell in row))
    return "\n".join(rows)


def build_input_coord(
    grid_size: Tuple[int, int],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    obstacles: List[Tuple[int, int]],
) -> str:
    """Build natural-language coordinate description of the grid."""
    rows, cols = grid_size
    obs_str = ", ".join(f"({r},{c})" for r, c in sorted(obstacles))
    return (
        f"Grid {rows}x{cols}. "
        f"Start: (row={start[0]}, col={start[1]}). "
        f"Goal: (row={goal[0]}, col={goal[1]}). "
        f"Obstacles: [{obs_str}]."
    )


def is_valid_move(
    world: List[List[int]],
    pos: Tuple[int, int],
    action: str,
) -> Tuple[bool, Tuple[int, int]]:
    """Check if an action is valid from pos. Returns (is_valid, new_pos)."""
    rows = len(world)
    cols = len(world[0])
    dr, dc = ACTION_DELTAS[action]
    nr, nc = pos[0] + dr, pos[1] + dc
    if 0 <= nr < rows and 0 <= nc < cols and world[nr][nc] != OBSTACLE:
        return True, (nr, nc)
    return False, pos


def execute_actions(
    world: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    actions: List[str],
) -> dict:
    """Execute a list of actions and return evaluation results."""
    pos = start
    feasible = True
    for action in actions:
        valid, new_pos = is_valid_move(world, pos, action)
        if not valid:
            feasible = False
            break
        pos = new_pos

    success = pos == goal
    return {"success": success, "feasible": feasible, "final_pos": pos}
