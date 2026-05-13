# Failure Cases: 10x10_long / deepseek-v4-flash / few_shot

## Failure Distribution

| Failure Type | Count | Rate |
|---|---:|---:|
| parse_failure | 0 | 0.0000 |
| invalid_action | 0 | 0.0000 |
| out_of_bounds | 0 | 0.0000 |
| obstacle_collision | 0 | 0.0000 |
| wrong_goal | 0 | 0.0000 |
| suboptimal | 0 | 0.0000 |
| empty_output | 200 | 1.0000 |
| success | 0 | 0.0000 |

## Representative Cases

### empty_output

- id: `test_ood_000004`
- grid_size: `[10, 10]`
- start: `[9, 8]`
- goal: `[0, 0]`
- gold: `up left up up up up up up left left up left left left left up left`
- parsed: ``
- interpretation: The API returned no usable text for this sample.

Grid:

```text
G . # . . # # . . .
# . . . . . # . . .
# . . # # . . . # .
# # . # # . # . # .
# # . . # . # . . #
. # . . . . # . . .
# . . . . . . . # .
# . . . . . # . # #
. # # # . . . . . .
# # . . . . . # S .
```

Raw output:

```text
<EMPTY>
```

Execution trace:

```text
0: start [9, 8]
```
