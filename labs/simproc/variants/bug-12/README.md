# bug-12

> "Works on my machine. Does not work on my lab partner's, and we are running the
> same program on the same board. The only thing we set differently is the baud
> rate."

## What was seen

`uio_in` sets the UART bit period: `clk_per_bit = uio_in × 4`. Three people, three
settings, three different stories.

| `uio_in` | `clk_per_bit` | `PING` → | six bytes written and read back |
|---|---|---|---|
| 1 | 4 | `TimeoutError` — no reply at all | `TimeoutError` |
| 2 | 8 | `TimeoutError` | `TimeoutError` |
| 4 | 16 | `0xAA` — correct | `ValueError` |
| 8 | 32 | `0xAA` | 6/6 |
| 16 | 64 | `0xAA` | 6/6 |
| 32 | 128 | `0xAA` | 6/6 |
| 64 | 256 | `0xAA` | 6/6 |

At `clk_per_bit = 32` and above, this core is indistinguishable from a correct
one. The full ten-test suite scores 10/10 on it. Every program runs, every
result is right.

At `clk_per_bit = 16`, `PING` answers `0xAA` — the link's own health check says
the link is fine — and data does not survive the trip. (`ValueError` is cocotb
reporting that the byte it read back has bits that are neither 0 nor 1.)

## What you have

`src/`: the core, 1178 + 49 lines of SystemVerilog. One line of it is wrong.
`test/`: the testbench that shipped with this chip.

```bash
cd test && make -B
```

It passes — and so does everything else, if you only ever run at one baud rate.

## What finishing looks like

1. A test that fails on this core and would pass on a correct one.
2. The one-line fix.
3. That same test passing.

Two questions worth answering before you start reading code, because the answers
are the bug:

- Why does `PING` still work at `clk_per_bit = 16` when nothing else does?
  Look at the byte `PING` sends — `0xF0` — and at the byte it replies with.
- Why does the failure get *worse* as the bit period gets *shorter*?
