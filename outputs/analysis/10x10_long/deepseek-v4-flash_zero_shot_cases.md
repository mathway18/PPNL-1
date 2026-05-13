# Failure Cases: 10x10_long / deepseek-v4-flash / zero_shot

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 2 | 0.0100 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 0 | 0.0000 |
| empty_output | 139 | 0.6950 |
| success | 59 | 0.2950 |

## Representative Cases

### obstacle_collision

- id: `test_ood_000027`
- grid_size: `[10, 10]`
- start: `[3, 4]`
- goal: `[9, 8]`
- gold: `up right right right right down down down down down left down down right`
- parsed: `up right right right right right down down left down down down down right`
- interpretation: The action sequence moves into an obstacle cell.

Grid:

```text
# # . . . # . . . .
. . . . # . # . . .
. . . . . . . . . #
. . . # S # # # . .
. . . . # . . . . .
. # . . . . . . . #
. . . . . . . . . .
. . # . # . . . . .
. . . # # . # . # .
. . # . . . . . G .
```

Raw output:

```text
up right right right right right down down left down down down down right
```

Execution trace:

```text
0: start [3, 4]
1: up -> [2, 4] (ok)
2: right -> [2, 5] (ok)
3: right -> [2, 6] (ok)
4: right -> [2, 7] (ok)
5: right -> [2, 8] (ok)
6: right -> [2, 9] (obstacle_collision)
```

### empty_output

- id: `test_ood_000062`
- grid_size: `[10, 10]`
- start: `[3, 1]`
- goal: `[8, 1]`
- gold: `right down right right right right down down down right right right down down left left left left left left left up left`
- parsed: ``
- interpretation: The API returned no usable text for this sample.

Grid:

```text
. . . . . . . # . .
# . . # . # . . . .
. . . . . . # # # #
# S . # . . # . # .
. # . . . . . . . .
. # . . . # . # . #
. # . # . # . . . .
. . # # . # . . . .
# G . # # . # # # .
. . . . . . . . . .
```

Raw output:

```text
<EMPTY>
```

Execution trace:

```text
0: start [3, 1]
```

### success

- id: `test_ood_000004`
- grid_size: `[10, 10]`
- start: `[9, 8]`
- goal: `[0, 0]`
- gold: `up left up up up up up up left left up left left left left up left`
- parsed: `up left up up left left up up up up up left left left left up left`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
G . # . . # # . . .
# . . . . . # . . .
# . . # # . . . # .
# # . # # . # . # .
# # . . # . # . . #
. # . . . . # . . .
# . . . . . . . # .
# . . . . . # . # #
. # # # . . . . . .
# # . . . . . # S .
```

Raw output:

```text
up left up up left left up up up up up left left left left up left
```

Execution trace:

```text
0: start [9, 8]
1: up -> [8, 8] (ok)
2: left -> [8, 7] (ok)
3: up -> [7, 7] (ok)
4: up -> [6, 7] (ok)
5: left -> [6, 6] (ok)
6: left -> [6, 5] (ok)
7: up -> [5, 5] (ok)
8: up -> [4, 5] (ok)
9: up -> [3, 5] (ok)
10: up -> [2, 5] (ok)
11: up -> [1, 5] (ok)
... 6 more steps
```
