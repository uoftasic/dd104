# bug-01

> "I've been using this core all week and it's been fine. I clear registers with
> `SUB r0,r0` constantly and that always works. Today I subtracted 2 from 9 and
> got **249**."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 9            R0 = 9
SUB r1,r1        R1 = 0
ADD r1,r0        R1 = 9
SUB r0,r0        R0 = 0
ORI 2            R0 = 2
SUB r1,r0        R1 = R1 - R0
```

| | R0 | R1 |
|---|---|---|
| should be | 2 | **7** |
| this core | 2 | **249** |

249 is not garbage. 256 − 249 = 7, so the machine computed −7 and wrapped it into
eight bits. It got the right magnitude and the wrong sign.

Every other instruction in that program behaved.

## What you have

`src/` — the core: 1178 + 49 lines of SystemVerilog. One line of it is wrong.
`test/` — the testbench that shipped with this chip.

```bash
cd test && make -B
```

It passes. It also passed before anyone touched this core, which tells you
something about what it is actually checking.

## What finishing looks like

1. A test that **fails** on this core and would pass on a correct one.
2. The one-line fix.
3. That same test passing.

In that order. A fix with no failing test in front of it is a guess that happened
to work.
