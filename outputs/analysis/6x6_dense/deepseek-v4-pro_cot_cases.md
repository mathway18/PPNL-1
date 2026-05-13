# Failure Cases: 6x6_dense / deepseek-v4-pro / cot

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 1 | 0.0050 |
| empty_output | 0 | 0.0000 |
| success | 199 | 0.9950 |

## Representative Cases

### suboptimal

- id: `test_ood_000147`
- grid_size: `[6, 6]`
- start: `[2, 5]`
- goal: `[3, 1]`
- gold: `left left up left left down down`
- parsed: `left left up left left left down right down`
- interpretation: The path reaches the goal but is longer than the shortest path (9 vs 7).

Grid:

```text
# . . . # .
. . . . # #
. . # . . S
# G # # # .
. . # # # .
. . . # . #
```

Raw output:

```text
Reasoning: Start at (2,5). Goal at (3,1). Direct left on row 2 is blocked by obstacle at (2,2). Down to row 3 is blocked by obstacles at (3,4). So we go left to (2,4), left to (2,3), then up to (1,3) to bypass obstacles, then left across row 1 to (1,0), down to (2,0), right to (2,1), and finally down to goal (3,1). All moves avoid obstacles and stay within bounds.
FINAL: left left up left left left down right down
```

Execution trace:

```text
0: start [2, 5]
1: left -> [2, 4] (ok)
2: left -> [2, 3] (ok)
3: up -> [1, 3] (ok)
4: left -> [1, 2] (ok)
5: left -> [1, 1] (ok)
6: left -> [1, 0] (ok)
7: down -> [2, 0] (ok)
8: right -> [2, 1] (ok)
9: down -> [3, 1] (ok)
```

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
Reasoning: The start is at (5,4) and the goal is at (5,5), directly to the right. There are no obstacles between them; (5,4) and (5,5) are both free. A single "right" action reaches the goal safely and directly.

FINAL: right
```

Execution trace:

```text
0: start [5, 4]
1: right -> [5, 5] (ok)
```
