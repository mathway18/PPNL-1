# Failure Cases: 6x6_dense / deepseek-v4-flash / few_shot

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

- id: `test_ood_000007`
- grid_size: `[6, 6]`
- start: `[5, 4]`
- goal: `[5, 5]`
- gold: `right`
- parsed: `right`
- interpretation: The path is feasible, reaches the goal, and is shortest-length.

Grid:

```text
# # # . . #
. # . . # .
. # . . . #
. . # # . .
# . . . . .
. # # # S G
```

Raw output:

```text
right
```

Execution trace:

```text
0: start [5, 4]
1: right -> [5, 5] (ok)
```
