# Failure Cases: 6x6_dense / google-flan-t5-base_6x6 / finetune

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 109 | 0.5450 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 91 | 0.4550 |

## Representative Cases

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
