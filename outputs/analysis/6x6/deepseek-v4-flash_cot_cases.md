# Failure Cases: 6x6 / deepseek-v4-flash / cot

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
Reasoning: The start position is at (3,1) and the goal is at (3,0), which is immediately to the left. There are no obstacles between them; the nearest obstacles are at (0,0), (2,5), and (5,2), which do not interfere. Therefore, a single left move reaches the goal.

FINAL: left
```

Execution trace:

```text
0: start [3, 1]
1: left -> [3, 0] (ok)
```
