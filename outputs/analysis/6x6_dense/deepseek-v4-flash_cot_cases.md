# Failure Cases: 6x6_dense / deepseek-v4-flash / cot

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 1 | 0.0050 |
| empty_output | 0 | 0.0000 |
| success | 199 | 0.9950 |

## Representative Cases

### suboptimal

- id: `test_ood_000021`
- grid_size: `[6, 6]`
- start: `[1, 5]`
- goal: `[5, 0]`
- gold: `left left left up left left down down down down down`
- parsed: `up left down left left up left left down down down down down`
- interpretation: The path reaches the goal but is longer than the shortest path (13 vs 11).

Grid:

```text
. . . # . .
. # . . . S
. . # # # .
. . . # # .
. # # . . #
G . . . # #
```

Raw output:

```text
Reasoning: The start is at (1,5) and goal at (5,0). A direct path downward and left is blocked by obstacles including (2,2), (2,3), (2,4), (3,3), (3,4), (4,1), (4,2), and (4,5). A safe route goes up from start to (0,5), then left to (0,4), down to (1,4), left to (1,3), left to (1,2), up to (0,2), left to (0,1), left to (0,0), then down repeatedly to (5,0). This path avoids all obstacles.

FINAL: up left down left left up left left down down down down down
```

Execution trace:

```text
0: start [1, 5]
1: up -> [0, 5] (ok)
2: left -> [0, 4] (ok)
3: down -> [1, 4] (ok)
4: left -> [1, 3] (ok)
5: left -> [1, 2] (ok)
6: up -> [0, 2] (ok)
7: left -> [0, 1] (ok)
8: left -> [0, 0] (ok)
9: down -> [1, 0] (ok)
10: down -> [2, 0] (ok)
11: down -> [3, 0] (ok)
... 2 more steps
```

### success

- id: `test_ood_000008`
- grid_size: `[6, 6]`
- start: `[0, 2]`
- goal: `[1, 2]`
- gold: `down`
- parsed: `down`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
# . S . # .
. # G . . .
# . . . # .
# # . . . #
# # . # . .
# . . . # #
```

Raw output:

```text
Reasoning: Start at (0,2) and goal at (1,2). The cell directly below the start is the goal, and there are no obstacles blocking this move. Therefore, the only action needed is down.

FINAL: down
```

Execution trace:

```text
0: start [0, 2]
1: down -> [1, 2] (ok)
```
