# Failure Cases: 6x6_dense / deepseek-v4-flash / plan_verify

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 1 | 0.0050 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 5 | 0.0250 |
| empty_output | 0 | 0.0000 |
| success | 194 | 0.9700 |

## Representative Cases

### parse_failure

- id: `test_ood_000173`
- grid_size: `[6, 6]`
- start: `[5, 0]`
- goal: `[0, 0]`
- gold: `right up up up up up left`
- parsed: ``
- interpretation: The output did not contain any valid action tokens.

Grid:

```text
G . . . # .
# . . # . #
# . # . . #
. . . # . #
# . . # # .
S . # . # .
```

Raw output:

```text
FINAL: R U U U U U L
```

Execution trace:

```text
0: start [5, 0]
```

### suboptimal

- id: `test_ood_000075`
- grid_size: `[6, 6]`
- start: `[2, 2]`
- goal: `[4, 4]`
- gold: `down right right down`
- parsed: `down right right right down left`
- interpretation: The path reaches the goal but is longer than the shortest path (6 vs 4).

Grid:

```text
. . # # . #
. . # # . .
# . S # # .
. # . . . .
. # . # G .
. # # # . #
```

Raw output:

```text
FINAL: down, right, right, right, down, left
```

Execution trace:

```text
0: start [2, 2]
1: down -> [3, 2] (ok)
2: right -> [3, 3] (ok)
3: right -> [3, 4] (ok)
4: right -> [3, 5] (ok)
5: down -> [4, 5] (ok)
6: left -> [4, 4] (ok)
```

### success

- id: `test_ood_000008`
- grid_size: `[6, 6]`
- start: `[0, 2]`
- goal: `[1, 2]`
- gold: `down`
- parsed: `down`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
# . S . # .
. # G . . .
# . . . # .
# # . . . #
# # . # . .
# . . . # #
```

Raw output:

```text
FINAL: down
```

Execution trace:

```text
0: start [0, 2]
1: down -> [1, 2] (ok)
```
