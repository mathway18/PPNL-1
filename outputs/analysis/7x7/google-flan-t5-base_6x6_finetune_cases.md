# Failure Cases: 7x7 / google-flan-t5-base_6x6 / finetune

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 98 | 0.4900 |
| wrong_goal | 2 | 0.0100 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 100 | 0.5000 |

## Representative Cases

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

- id: `test_ood_000087`
- grid_size: `[7, 7]`
- start: `[0, 6]`
- goal: `[6, 0]`
- gold: `down down down down down left left left left down left left`
- parsed: `down down down left left left left`
- interpretation: The path is feasible but ends at [3, 2] instead of the goal.

Grid:

```text
# . . . . . S
. # . . # # .
. # . . . . .
. . . . . . .
. . . . . . .
# . . . . . .
G . . # . . .
```

Raw output:

```text
down down down left left left left
```

Execution trace:

```text
0: start [0, 6]
1: down -> [1, 6] (ok)
2: down -> [2, 6] (ok)
3: down -> [3, 6] (ok)
4: left -> [3, 5] (ok)
5: left -> [3, 4] (ok)
6: left -> [3, 3] (ok)
7: left -> [3, 2] (ok)
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
