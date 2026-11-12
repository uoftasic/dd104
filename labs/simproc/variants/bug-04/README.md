# bug-04

> "Half my program works. The half that works is the half where I do things to a
> register using itself."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 5            R0 = 5
SUB r1,r1        R1 = 0
ADD r1,r0        R1 = R1 + R0
SUB r0,r0        R0 = 0
ORI 2            R0 = 2
ADD r1,r0        R1 = R1 + R0
```

| | R0 | R1 |
|---|---|---|
| should be | 2 | 7 |
| this core | 2 | 0 |

R1 never changes. Not once, in either `ADD`. And yet `SUB r1,r1` clearly worked —
R1 was already 0, so who can tell.

`LOAD` still writes the register you name. That is worth knowing before you
start looking.

## What you have

`src/`: the core, 1178 + 49 lines of SystemVerilog. One line of it is wrong.
`test/`: the testbench that shipped with this chip.

```bash
cd test && make -B
```

It passes.

## What finishing looks like

1. A test that fails on this core and would pass on a correct one.
2. The one-line fix.
3. That same test passing.

Seven of a ten-test suite catch this one. Three do not. Work out why those three
do not and you will have found it before you open the source.
