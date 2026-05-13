# Failure Cases: 7x7 / google-flan-t5-small_6x6 / finetune

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 2 | 0.0100 |
| obstacle_collision | 100 | 0.5000 |
| wrong_goal | 6 | 0.0300 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 92 | 0.4600 |

## Representative Cases

### out_of_bounds

- id: `test_ood_000017`
- grid_size: `[7, 7]`
- start: `[1, 2]`
- goal: `[6, 0]`
- gold: `down down down down down left left`
- parsed: `down down down down left left left`
- interpretation: The action sequence attempts to leave the grid.

Grid:

```text
. . . . . . .
. # S . . # .
. # . # . . .
. . . . . . .
. . . . . . #
. . . . . . .
G . . # . . .
```

Raw output:

```text
down down down down left left left
```

Execution trace:

```text
0: start [1, 2]
1: down -> [2, 2] (ok)
2: down -> [3, 2] (ok)
3: down -> [4, 2] (ok)
4: down -> [5, 2] (ok)
5: left -> [5, 1] (ok)
6: left -> [5, 0] (ok)
7: left -> [5, -1] (out_of_bounds)
```

### obstacle_collision

- id: `test_ood_000001`
- grid_size: `[7, 7]`
- start: `[0, 4]`
- goal: `[3, 1]`
- gold: `down down left left down left`
- parsed: `down down down left left left`
- interpretation: The action sequence moves into an obstacle cell.

Grid:

```text
. . . . S . .
. . . . . . #
. . . . . . .
. G . # . . #
. . . . . . .
. # # # . . .
# # # . . . #
```

Raw output:

```text
down down down left left left
```

Execution trace:

```text
0: start [0, 4]
1: down -> [1, 4] (ok)
2: down -> [2, 4] (ok)
3: down -> [3, 4] (ok)
4: left -> [3, 3] (obstacle_collision)
```

### wrong_goal

- id: `test_ood_000033`
- grid_size: `[7, 7]`
- start: `[0, 6]`
- goal: `[6, 1]`
- gold: `down down down down left left down left down left left`
- parsed: `down down down down left left left left left`
- interpretation: The path is feasible but ends at [4, 1] instead of the goal.

Grid:

```text
. . . . . # S
. . . . . . .
. . . . . . .
. . # # # . .
. . . . . . .
. # . . . # .
. G . . # . .
```

Raw output:

```text
down down down down left left left left left
```

Execution trace:

```text
0: start [0, 6]
1: down -> [1, 6] (ok)
2: down -> [2, 6] (ok)
3: down -> [3, 6] (ok)
4: down -> [4, 6] (ok)
5: left -> [4, 5] (ok)
6: left -> [4, 4] (ok)
7: left -> [4, 3] (ok)
8: left -> [4, 2] (ok)
9: left -> [4, 1] (ok)
```

### success

- id: `test_ood_000004`
- grid_size: `[7, 7]`
- start: `[3, 5]`
- goal: `[2, 5]`
- gold: `up`
- parsed: `up`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
. # . # . . .
# . . . . . .
# . . . . G #
# . # . . S .
# . . . . . .
. . . . . . .
. . . . # . #
```

Raw output:

```text
up
```

Execution trace:

```text
0: start [3, 5]
1: up -> [2, 5] (ok)
```
