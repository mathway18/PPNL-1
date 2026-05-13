# Failure Cases: 6x6_dense / google-flan-t5-small_6x6 / finetune

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 1 | 0.0050 |
| obstacle_collision | 110 | 0.5500 |
| wrong_goal | 1 | 0.0050 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 88 | 0.4400 |

## Representative Cases

### out_of_bounds

- id: `test_ood_000197`
- grid_size: `[6, 6]`
- start: `[2, 4]`
- goal: `[2, 0]`
- gold: `left left left left`
- parsed: `left left left left left`
- interpretation: The action sequence attempts to leave the grid.

Grid:

```text
. # . . . #
# # . # . #
G . . . S #
. . . . # .
. # # # # #
# . . . # .
```

Raw output:

```text
left left left left left
```

Execution trace:

```text
0: start [2, 4]
1: left -> [2, 3] (ok)
2: left -> [2, 2] (ok)
3: left -> [2, 1] (ok)
4: left -> [2, 0] (ok)
5: left -> [2, -1] (out_of_bounds)
```

### obstacle_collision

- id: `test_ood_000001`
- grid_size: `[6, 6]`
- start: `[5, 4]`
- goal: `[4, 3]`
- gold: `right up up left left down`
- parsed: `up left`
- interpretation: The action sequence moves into an obstacle cell.

Grid:

```text
# . # # # .
. # . # . #
. # # . . .
# . . . . .
. . . G # .
# . # # S .
```

Raw output:

```text
up left
```

Execution trace:

```text
0: start [5, 4]
1: up -> [4, 4] (obstacle_collision)
```

### wrong_goal

- id: `test_ood_000076`
- grid_size: `[6, 6]`
- start: `[4, 5]`
- goal: `[4, 1]`
- gold: `left left left left`
- parsed: `left left left left left`
- interpretation: The path is feasible but ends at [4, 0] instead of the goal.

Grid:

```text
. . . . . #
# # # . . #
. . . # # #
. . # # # .
. G . . . S
. # . # . #
```

Raw output:

```text
left left left left left
```

Execution trace:

```text
0: start [4, 5]
1: left -> [4, 4] (ok)
2: left -> [4, 3] (ok)
3: left -> [4, 2] (ok)
4: left -> [4, 1] (ok)
5: left -> [4, 0] (ok)
```

### success

- id: `test_ood_000002`
- grid_size: `[6, 6]`
- start: `[1, 2]`
- goal: `[2, 2]`
- gold: `down`
- parsed: `down`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
. . # # # .
# # S . . #
# # G # . .
# . . . . #
. # # . . .
# . . . . .
```

Raw output:

```text
down
```

Execution trace:

```text
0: start [1, 2]
1: down -> [2, 2] (ok)
```
