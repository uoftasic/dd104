# bug-11

> "My constant-building code produces zero. Not a wrong constant — zero. And the
> exact same three lines worked in the program I wrote yesterday."

## What was seen

```
SUB r0,r0        R0 = 0
SUB r1,r1        R1 = 0
ORI 5            R0 = R0 | 5
ORI 3            R0 = R0 | 3
```

| | R0 |
|---|---|
| should be | **7** |
| this core | **0** |

And with a single `ORI`, straight out of reset:

```
SUB r0,r0
SUB r1,r1
ORI 5            R0 = R0 | 5
```

| | R0 |
|---|---|
| should be | **5** |
| this core | **0** |

The value 5 is not lost. It exists in the machine. It is just not in R0.

Nothing else in the program misbehaves: the `SUB`s clear what they are told to
clear, `ADD` adds, `LOAD` and `STORE` are exact.

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

`ORI` is the only instruction in this machine with no register field in it — the
opcode is three bits and all five remaining bits are the immediate. So the
register it works on is not in the instruction. It is in the hardware, and it has
to be named in two separate places.
