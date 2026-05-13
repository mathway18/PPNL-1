# Failure Cases: 6x6 / deepseek-v4-pro / plan_verify

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 2 | 0.0100 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 7 | 0.0350 |
| empty_output | 0 | 0.0000 |
| success | 191 | 0.9550 |

## Representative Cases

### parse_failure

- id: `test_iid_000091`
- grid_size: `[6, 6]`
- start: `[5, 5]`
- goal: `[0, 0]`
- gold: `left up left left left up up up up left`
- parsed: ``
- interpretation: The output did not contain any valid action tokens.

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
FINAL: LLLULUUUUL
```

Execution trace:

```text
0: start [5, 5]
```

### suboptimal

- id: `test_iid_000015`
- grid_size: `[6, 6]`
- start: `[5, 2]`
- goal: `[0, 1]`
- gold: `up up up left up up`
- parsed: `left left up up up up up right`
- interpretation: The path reaches the goal but is longer than the shortest path (8 vs 6).

Grid:

```text
. G . . . .
. . # . # .
. . . . . .
. . . . . .
. . . . . .
. . S . # .
```

Raw output:

```text
FINAL: left, left, up, up, up, up, up, right
```

Execution trace:

```text
0: start [5, 2]
1: left -> [5, 1] (ok)
2: left -> [5, 0] (ok)
3: up -> [4, 0] (ok)
4: up -> [3, 0] (ok)
5: up -> [2, 0] (ok)
6: up -> [1, 0] (ok)
7: up -> [0, 0] (ok)
8: right -> [0, 1] (ok)
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
FINAL: left
```

Execution trace:

```text
0: start [3, 1]
1: left -> [3, 0] (ok)
```
