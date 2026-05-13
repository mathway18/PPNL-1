# Failure Cases: 6x6 / google-flan-t5-small_6x6 / finetune

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 1 | 0.0050 |
| obstacle_collision | 75 | 0.3750 |
| wrong_goal | 1 | 0.0050 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 123 | 0.6150 |

## Representative Cases

### out_of_bounds

- id: `test_iid_000046`
- grid_size: `[6, 6]`
- start: `[5, 5]`
- goal: `[0, 5]`
- gold: `up up up up up`
- parsed: `up up up up up up`
- interpretation: The action sequence attempts to leave the grid.

Grid:

```text
. . . . . G
. . . . . .
. . . # . .
. . . . . .
. . # . . .
. . # . . S
```

Raw output:

```text
up up up up up up
```

Execution trace:

```text
0: start [5, 5]
1: up -> [4, 5] (ok)
2: up -> [3, 5] (ok)
3: up -> [2, 5] (ok)
4: up -> [1, 5] (ok)
5: up -> [0, 5] (ok)
6: up -> [-1, 5] (out_of_bounds)
```

### obstacle_collision

- id: `test_iid_000005`
- grid_size: `[6, 6]`
- start: `[1, 3]`
- goal: `[4, 0]`
- gold: `down down down down left left up left`
- parsed: `down down down left left left`
- interpretation: The action sequence moves into an obstacle cell.

Grid:

```text
. . . . . .
# . . S # .
# . . . . .
# # . . . .
G . # . . #
# . . . . .
```

Raw output:

```text
down down down left left left
```

Execution trace:

```text
0: start [1, 3]
1: down -> [2, 3] (ok)
2: down -> [3, 3] (ok)
3: down -> [4, 3] (ok)
4: left -> [4, 2] (obstacle_collision)
```

### wrong_goal

- id: `test_iid_000095`
- grid_size: `[6, 6]`
- start: `[3, 5]`
- goal: `[3, 1]`
- gold: `left left left left`
- parsed: `left left left left left`
- interpretation: The path is feasible but ends at [3, 0] instead of the goal.

Grid:

```text
. . . . . .
. # # . . .
. # . . . #
. G . . . S
. . . . . .
. . . . . .
```

Raw output:

```text
left left left left left
```

Execution trace:

```text
0: start [3, 5]
1: left -> [3, 4] (ok)
2: left -> [3, 3] (ok)
3: left -> [3, 2] (ok)
4: left -> [3, 1] (ok)
5: left -> [3, 0] (ok)
```

### success

- id: `test_iid_000001`
- grid_size: `[6, 6]`
- start: `[5, 2]`
- goal: `[4, 4]`
- gold: `up right right`
- parsed: `up right right`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
. . . . . .
# . . . . .
. # . . . #
. . . . # .
. # . . G .
. . S . . .
```

Raw output:

```text
up right right
```

Execution trace:

```text
0: start [5, 2]
1: up -> [4, 2] (ok)
2: right -> [4, 3] (ok)
3: right -> [4, 4] (ok)
```
