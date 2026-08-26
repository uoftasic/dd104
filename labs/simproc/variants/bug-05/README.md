# bug-05

> "Skipping an instruction works perfectly. Looping does not. My loop runs its
> body once and then the program wanders off somewhere I never sent it."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 1            R0 = 1
SUB r1,r1        R1 = 0
ADD r1,r0        R1 = 1        -- the decrement
SUB r0,r0        R0 = 0
ORI 3            R0 = 3        -- the counter
SUB r0,r1        R0 = R0 - 1   <- loop body
BNZ -2           back to the line above, while R0 != 0
```

| | R0 at the end |
|---|---|
| should be | **0** — the body runs three times |
| this core | **2** — the body ran once |

After that single pass the PC is nowhere near the loop.

Sweeping all sixteen displacements a `JMP` can encode, from an instruction at
address 20:

| displacement | should land on | this core lands on |
|---|---|---|
| `+0` … `+7` | 21 … 28 | **21 … 28, every one correct** |
| `-1` | 20 | 36 |
| `-2` | 19 | 35 |
| `-3` | 18 | 34 |
| `-8` | 13 | 29 |

Every forward branch is exactly right. Every backward branch lands sixteen too
far forward.

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

The displacement field is four bits. There are exactly sixteen branch targets a
program can ask for. Sixteen is a small enough number to try all of them, and a
test that tries all of them is not a clever test — it is just the obvious one.
