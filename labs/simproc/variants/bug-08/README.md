# bug-08

> "Every number this core produces is correct. I have checked the registers, the
> flags, the program counter and all 64 bytes of memory against a model, on
> twenty different programs. All correct. And my scoreboard has gone quiet."

## What was seen

The chip has a `done` pin — `uo_out[2]` — that pulses high for exactly one cycle
each time an instruction retires. A scoreboard that samples architectural state
on that pulse is the normal way to check a core instruction by instruction.

A fourteen-instruction program, three of them `STORE`:

```
SUB r0,r0 ; ORI 16 ; SUB r2,r2 ; ADD r2,r0 ; ADD r2,r0    R2 = 32
SUB r0,r0 ; ORI 7  ; SUB r1,r1 ; ADD r1,r0                R1 = 7
STORE r1,r2 ; ADD r1,r0 ; STORE r1,r2 ; ADD r1,r0 ; STORE r1,r2
```

| | instructions retired | `done` pulses |
|---|---|---|
| should be | 14 | 14 |
| this core | 14 | 11 |

`mem[32]` ends at 21 and R1 ends at 21, both correct. The core executes all
fourteen instructions and the fourteenth one finishes. Three pulses are simply
not there.

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

Think about what this bug does to a scoreboard that triggers on `done`. It does
not make it report a mismatch. It makes it stop looking, and report nothing at
all, which is what a passing test looks like from the outside.
