# bug-09

> "One compare, one branch: perfect. One compare, two branches: the second branch
> is nonsense. I don't have a compare instruction, I use `SUB`, and I know the
> result is still sitting in the register — I checked."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 4            R0 = 4
SUB r0,r0        R0 = 0        <- the "compare": result is zero, so Z is set
BZ  +1           taken, skips the next instruction
ORI 16           skipped, correctly
BNZ +1           must NOT be taken -- Z is still set
ORI 8            R0 = 8
```

| | R0 |
|---|---|
| should be | 8 — `BNZ` is not taken, so the `ORI 8` runs |
| this core | 0 — `BNZ` was taken and skipped it |

The first branch does the right thing. The second branch, reading the same
comparison, does the opposite of the right thing.

Nothing between them writes a register or does any arithmetic you asked for.

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

"The comparison is still valid" is an assumption. Write the test that checks it.
