# Failure Cases: 5x5 / google-flan-t5-small_6x6 / finetune

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 61 | 0.3050 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 139 | 0.6950 |

## Representative Cases

### obstacle_collision

- id: `test_ood_000001`
- grid_size: `[5, 5]`
- start: `[0, 3]`
- goal: `[3, 2]`
- gold: `down down left down`
- parsed: `down down down left`
- interpretation: The action sequence moves into an obstacle cell.

Grid:

```text
. . . S .
. . . . .
# . . . .
. . G # .
. . . . .
```

Raw output:

```text
down down down left
```

Execution trace:

```text
0: start [0, 3]
1: down -> [1, 3] (ok)
2: down -> [2, 3] (ok)
3: down -> [3, 3] (obstacle_collision)
```

### success

- id: `test_ood_000002`
- grid_size: `[5, 5]`
- start: `[4, 4]`
- goal: `[0, 3]`
- gold: `up up up up left`
- parsed: `up up up up left`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
. . # G .
. . . # .
# . . . .
. # . . .
. # . . S
```

Raw output:

```text
up up up up left
```

Execution trace:

```text
0: start [4, 4]
1: up -> [3, 4] (ok)
2: up -> [2, 4] (ok)
3: up -> [1, 4] (ok)
4: up -> [0, 4] (ok)
5: left -> [0, 3] (ok)
```
