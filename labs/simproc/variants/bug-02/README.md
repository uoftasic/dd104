# bug-02

> "NAND is the only bitwise instruction this thing has, so I use it for
> everything. `NAND rX,rX` gives me NOT and that's been perfect. Then I tried it
> on two different values and the answer was nowhere near right."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 3            R0 = 0x03
SHL r0,2         R0 = 0x0C
SHL r0,2         R0 = 0x30
ORI 3            R0 = 0x33
SUB r1,r1        R1 = 0
ADD r1,r0        R1 = 0x33
SUB r0,r0        R0 = 0
ORI 15           R0 = 0x0F
NAND r1,r0       R1 = NAND(0x33, 0x0F)
```

| | R1 |
|---|---|
| should be | 0xFC (252) |
| this core | 0xC0 (192) |

`~(0x33 & 0x0F)` is `~0x03` = `0xFC`. The core returned `0xC0`.

The shifts and the ORIs on the way in are all correct — check them if you want,
they are.

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

Before you write that test, write down what inputs you would have picked if
nobody had told you the answer was wrong. Then check whether your own choice
would have caught it.
