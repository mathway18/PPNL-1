# Failure Cases: 6x6 / deepseek-v4-pro / cot

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 3 | 0.0150 |
| empty_output | 0 | 0.0000 |
| success | 197 | 0.9850 |

## Representative Cases

### suboptimal

- id: `test_iid_000037`
- grid_size: `[6, 6]`
- start: `[5, 4]`
- goal: `[2, 0]`
- gold: `up up left left left up left`
- parsed: `up up up left up left left left down`
- interpretation: The path reaches the goal but is longer than the shortest path (9 vs 7).

Grid:

```text
. # # . . .
. . . . # .
G . # . . .
. . . . . .
. . . . . .
. . # . S .
```

Raw output:

```text
Reasoning: The start is at (5,4) and the goal is at (2,0). The Manhattan distance is 7, but obstacles force a detour around (2,2) and (1,4). The direct path left from (2,4) is blocked by (2,2), and moving up from (2,4) is blocked by (1,4). Therefore, the shortest path goes up three times from (5,4) to (2,4), left to (2,3), up to (1,3) to bypass the obstacle, then left three times to (1,0), and finally down to the goal at (2,0). This route avoids all obstacles and takes 9 moves, which is optimal.

FINAL: up up up left up left left left down
```

Execution trace:

```text
0: start [5, 4]
1: up -> [4, 4] (ok)
2: up -> [3, 4] (ok)
3: up -> [2, 4] (ok)
4: left -> [2, 3] (ok)
5: up -> [1, 3] (ok)
6: left -> [1, 2] (ok)
7: left -> [1, 1] (ok)
8: left -> [1, 0] (ok)
9: down -> [2, 0] (ok)
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
Reasoning: The start position is at (3,1) and the goal is at (3,0), immediately to the left. There are no obstacles between them—the cell (3,0) is the goal and is not blocked. The other obstacles at (0,0), (2,5), and (5,2) are far from this direct path. The safest and shortest route is a single move left.

FINAL: left
```

Execution trace:

```text
0: start [3, 1]
1: left -> [3, 0] (ok)
```
