# Failure Cases: 6x6 / deepseek-v4-flash / zero_shot

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
