# Failure Cases: 6x6 / deepseek-v4-flash / plan_verify

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 1 | 0.0050 |
| suboptimal | 4 | 0.0200 |
| empty_output | 0 | 0.0000 |
| success | 195 | 0.9750 |

## Representative Cases

### wrong_goal

- id: `test_iid_000029`
- grid_size: `[6, 6]`
- start: `[1, 2]`
- goal: `[0, 3]`
- gold: `up right`
- parsed: `up left`
- interpretation: The path is feasible but ends at [0, 1] instead of the goal.

Grid:

```text
. . . G . #
. # S . . .
. . . # # .
. # # . . .
. # . . # .
. . . . . .
```

Raw output:

```text
Proposed action sequence: up, left.

Simulation:
- Start at (1,2).
- Step 1: up → (0,2). Grid boundary? Row 0 is within 0-5. No obstacle? (0,2) is empty.
- Step 2: left → (0,3). Goal reached.

Checks:
- No step leaves the grid (valid rows and columns).
- No step hits an obstacle (positions (0,2) and (0,3) are free, and (0,3) is goal).
- Final position matches goal.

Path is valid.

FINAL: up, left
```

Execution trace:

```text
0: start [1, 2]
1: up -> [0, 2] (ok)
2: left -> [0, 1] (ok)
```

### suboptimal

- id: `test_iid_000024`
- grid_size: `[6, 6]`
- start: `[1, 0]`
- goal: `[4, 3]`
- gold: `up right right down down down down right`
- parsed: `up right right right down right down down down left`
- interpretation: The path reaches the goal but is longer than the shortest path (10 vs 8).

Grid:

```text
. . . . . .
S # . . . #
# . . # . .
. . . . . #
. . . G . #
# . # . . .
```

Raw output:

```text
FINAL: up, right, right, right, down, right, down, down, down, left
```

Execution trace:

```text
0: start [1, 0]
1: up -> [0, 0] (ok)
2: right -> [0, 1] (ok)
3: right -> [0, 2] (ok)
4: right -> [0, 3] (ok)
5: down -> [1, 3] (ok)
6: right -> [1, 4] (ok)
7: down -> [2, 4] (ok)
8: down -> [3, 4] (ok)
9: down -> [4, 4] (ok)
10: left -> [4, 3] (ok)
```

### success

- id: `test_iid_000002`
- grid_size: `[6, 6]`
- start: `[3, 1]`
- goal: `[3, 0]`
- gold: `left`
- parsed: `left`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
# . . . . .
. . . . . .
. . . . . #
G S . . . .
. . . . . .
. . # . . .
```

Raw output:

```text
FINAL: left
```

Execution trace:

```text
0: start [3, 1]
1: left -> [3, 0] (ok)
```
