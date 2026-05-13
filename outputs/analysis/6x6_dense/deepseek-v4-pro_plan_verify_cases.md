# Failure Cases: 6x6_dense / deepseek-v4-pro / plan_verify

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

- id: `test_ood_000051`
- grid_size: `[6, 6]`
- start: `[0, 0]`
- goal: `[4, 4]`
- gold: `right right down down down down right right`
- parsed: ``
- interpretation: The output did not contain any valid action tokens.

Grid:

```text
S . . . . #
# # . . # #
# . . # # #
# . . . # .
# . . . G .
. . # . # #
```

Raw output:

```text
FINAL: R R R D L D D D R R
```

Execution trace:

```text
0: start [0, 0]
```

### suboptimal

- id: `test_ood_000001`
- grid_size: `[6, 6]`
- start: `[5, 4]`
- goal: `[4, 3]`
- gold: `right up up left left down`
- parsed: `right up up left left left left down right right`
- interpretation: The path reaches the goal but is longer than the shortest path (10 vs 6).

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
1. Candidate action sequence: right, up, up, left, left, left, left, down, right, right.

2. Simulate step by step:
   - Start: (5,4)
   - right → (5,5) [within grid, free]
   - up → (4,5) [within grid, free]
   - up → (3,5) [within grid, free]
   - left → (3,4) [within grid, free]
   - left → (3,3) [within grid, free]
   - left → (3,2) [within grid, free]
   - left → (3,1) [within grid, free]
   - down → (4,1) [within grid, free]
   - right → (4,2) [within grid, free]
   - right → (4,3) [goal reached]

3. Check bounds: All positions have row 0-5, col 0-5. None leave the grid.

4. Check obstacles: None of the visited cells are in the obstacle list [(0,0), (0,2), (0,3), (0,4), (1,1), (1,3), (1,5), (2,1), (2,2), (3,0), (4,4), (5,0), (5,2), (5,3)].

5. Goal reached: Final position is (4,3), which is the goal.

6. Path is valid, no revision needed.

FINAL: right, up, up, left, left, left, left, down, right, right
```

Execution trace:

```text
0: start [5, 4]
1: right -> [5, 5] (ok)
2: up -> [4, 5] (ok)
3: up -> [3, 5] (ok)
4: left -> [3, 4] (ok)
5: left -> [3, 3] (ok)
6: left -> [3, 2] (ok)
7: left -> [3, 1] (ok)
8: down -> [4, 1] (ok)
9: right -> [4, 2] (ok)
10: right -> [4, 3] (ok)
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
FINAL: right
```

Execution trace:

```text
0: start [5, 4]
1: right -> [5, 5] (ok)
```
