# bug-07

> "I keep a pointer in one register and load through it into another. I get back
> a number that is definitely in memory somewhere — it just isn't the one at the
> address I asked for."

## What was seen

`mem[40]` was loaded with `0x5A` (90) before the run.

```
SUB r0,r0        R0 = 0
ORI 8            R0 = 8
SHL r0,2         R0 = 32
ORI 8            R0 = 40        -- the address
SUB r1,r1        R1 = 0
ADD r1,r0        R1 = 40        -- the pointer
SUB r0,r0        R0 = 0         -- somewhere to put it
LOAD r0,r1       R0 = mem[R1]
```

| | R0 | R1 | mem[40] |
|---|---|---|---|
| should be | 90 | 40 | 90 |
| this core | 6 | 40 | 90 |

`mem[40]` still contains 90 afterwards, so nothing overwrote it. The pointer
register still contains 40. `STORE` puts things exactly where it is told.

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

A warning about this one, from someone who wrote the test suite it hides from:
the first `LOAD` test written for this core used the same register as pointer and
destination, because that is a real and common idiom. That test passes on this
core, and so do nine of the ten tests in the suite and six hundred random
instructions.
