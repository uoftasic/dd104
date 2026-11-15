# bug-13

> "There is nothing wrong with the answers. I am reporting this because the
> `halt` light flickers and it did not used to."

## What was seen

`uo_out[1]` is `halt`, which is high when the core is sitting in IDLE doing nothing.
While a program is running it should be low, continuously, from the `RUN` command
until the `HALT` command.

A fourteen-instruction program, three of them `STORE`:

```
SUB r0,r0 ; ORI 16 ; SUB r2,r2 ; ADD r2,r0 ; ADD r2,r0    R2 = 32
SUB r0,r0 ; ORI 7  ; SUB r1,r1 ; ADD r1,r0                R1 = 7
STORE r1,r2 ; ADD r1,r0 ; STORE r1,r2 ; ADD r1,r0 ; STORE r1,r2
```

| | R0 | R1 | R2 | mem[32] | `done` pulses | clocks with `halt` high while running |
|---|---|---|---|---|---|---|
| should be | 7 | 21 | 32 | 21 | 14 | 0 |
| this core | 7 | 21 | 32 | 21 | 14 | 3 |

Every architectural result is identical to a correct core: registers, memory,
flags, the program counter, the instruction count and the `done` count all match,
on every program tried.

There are three of those clocks, and the program has three `STORE`s.

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

This is the one where you have to decide whether it is a bug at all. Argue it
both ways before you look. Then consider: it costs one clock cycle per `STORE`,
forever, on every program this chip will ever run, and anyone debugging this
core through the `halt` pin sees the machine stop, three times, for no reason
they can name.
