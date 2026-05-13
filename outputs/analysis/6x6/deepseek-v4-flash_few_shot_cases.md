# Failure Cases: 6x6 / deepseek-v4-flash / few_shot

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 1 | 0.0050 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 0 | 0.0000 |
| empty_output | 0 | 0.0000 |
| success | 199 | 0.9950 |

## Representative Cases

### out_of_bounds

- id: `test_iid_000091`
- grid_size: `[6, 6]`
- start: `[5, 5]`
- goal: `[0, 0]`
- gold: `left up left left left up up up up left`
- parsed: `left left left up left left up up up left`
- interpretation: The action sequence attempts to leave the grid.

Grid:

```text
G . . . . #
. . . . # .
. . # # . .
. . # . . .
. . . . . #
. # . . . S
```

Raw output:

```text
left left left up left left up up up left
```

Execution trace:

```text
0: start [5, 5]
1: left -> [5, 4] (ok)
2: left -> [5, 3] (ok)
3: left -> [5, 2] (ok)
4: up -> [4, 2] (ok)
5: left -> [4, 1] (ok)
6: left -> [4, 0] (ok)
7: up -> [3, 0] (ok)
8: up -> [2, 0] (ok)
9: up -> [1, 0] (ok)
10: left -> [1, -1] (out_of_bounds)
```

### success

- id: `test_iid_000002`
- grid_size: `[6, 6]`
- start: `[3, 1]`
- goal: `[3, 0]`
- gold: `left`
- parsed: `left`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
# . . . . .
. . . . . .
. . . . . #
G S . . . .
. . . . . .
. . # . . .
```

Raw output:

```text
left
```

Execution trace:

```text
0: start [3, 1]
1: left -> [3, 0] (ok)
```
