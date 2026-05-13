# Failure Cases: 6x6 / deepseek-v4-pro / few_shot

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
