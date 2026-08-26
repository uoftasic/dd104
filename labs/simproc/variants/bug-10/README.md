# bug-10

> "`ORI` builds constants for me and it has never been wrong. It was wrong today
> and I cannot see the difference between today's program and every other one."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 5            R0 = R0 | 5
ORI 3            R0 = R0 | 3
```

| | R0 |
|---|---|
| should be | **7** — 5 is `0b00101`, 3 is `0b00011`, together `0b00111` |
| this core | **8** |

Eight. Not seven.

Every constant this student built before today came out right, and they were
building them the same way: `ORI` a few bits in, `ORI` a few more.

## What you have

`src/` — the core: 1178 + 49 lines of SystemVerilog. One line of it is wrong.
`test/` — the testbench that shipped with this chip.

```bash
cd test && make -B
```

It passes.

## What finishing looks like

1. A test that **fails** on this core and would pass on a correct one.
2. The one-line fix.
3. That same test passing.

Before you look at anything: `ORI 8 ; ORI 3` on this core gives **11**, which is
correct. `ORI 5 ; ORI 3` gives 8, which is not. Work out what is different about
those two programs and you are most of the way to the fix.
