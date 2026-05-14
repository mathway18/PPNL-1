# Failure Cases: 6x6 / google-flan-t5-base_6x6 / finetune

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 73 | 0.3650 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 127 | 0.6350 |

## Representative Cases

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
