# bug-06

> "Shifting by one is fine. I only noticed because I was building a constant and
> needed to shift by three."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 1            R0 = 1
SHL r0,2         R0 = 1 << 2
SUB r1,r1        R1 = 0
ADD r1,r0        R1 = R0        -- keep it
SUB r0,r0        R0 = 0
ORI 1            R0 = 1
SHL r0,3         R0 = 1 << 3
```

| | R0 (`1 << 3`) | R1 (`1 << 2`) |
|---|---|---|
| should be | **8** | **4** |
| this core | **2** | **1** |

`1 << 3` came back as 2, which is `1 << 1`. `1 << 2` came back as 1, which is
`1 << 0`.

Shifting right does the same thing. Building 64 by adding, then `SHR r1,3`:

| | R1 |
|---|---|
| should be | **8** |
| this core | **32** |

32 is `64 >> 1`.

Shift by 0 and shift by 1 are both correct, in both directions.

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

There are four encodable shift amounts and two directions. Eight cases. Test
eight cases.
