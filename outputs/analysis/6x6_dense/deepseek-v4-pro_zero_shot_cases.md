# Failure Cases: 6x6_dense / deepseek-v4-pro / zero_shot

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 200 | 1.0000 |

## Representative Cases

### success

- id: `test_ood_000001`
- grid_size: `[6, 6]`
- start: `[5, 4]`
- goal: `[4, 3]`
- gold: `right up up left left down`
- parsed: `right up up left left down`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

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
right up up left left down
```

Execution trace:

```text
0: start [5, 4]
1: right -> [5, 5] (ok)
2: up -> [4, 5] (ok)
3: up -> [3, 5] (ok)
4: left -> [3, 4] (ok)
5: left -> [3, 3] (ok)
6: down -> [4, 3] (ok)
```
