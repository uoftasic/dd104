# bug-12 — the UART RX bit period is one clock too long

Catalogue **B12**. Tier 5, Lab 06. The only bug in the set that is not in the CPU.

```diff
--- a/src/simproc_system.sv     line 1014, inside UART_RX
-                    if (clkCount < clk_per_bit - 1) begin
+                    if (clkCount < clk_per_bit) begin
```

Every received bit takes one clock too long, so the sample point walks later by
one clock per bit and is eight clocks late by bit 7.

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | **passes** |
| Suite at the lab default (`clk_per_bit = 32`) | **10/10 — completely hidden** |
| Suite at `clk_per_bit = 8` | **0/10 — nothing works at all** |
| Baud sweep | **fails** |

The sweep, seven bit periods, `PING` and a six-byte write/read round trip:

| `uio_in` | `clk_per_bit` | PING | bytes back |
|---|---|---|---|
| 1 | 4 | `TimeoutError` | `TimeoutError` |
| 2 | 8 | `TimeoutError` | `TimeoutError` |
| **4** | **16** | **`0xAA` — correct** | **`ValueError`** |
| 8 | 32 | `0xAA` | 6/6 |
| 16 | 64 | `0xAA` | 6/6 |
| 32 | 128 | `0xAA` | 6/6 |
| 64 | 256 | `0xAA` | 6/6 |

The clean core is `0xAA` and 6/6 at all seven.

## Why it hides

Set the labs' bus-functional model to `uio_in = 8` (`clk_per_bit = 32`) and this
core is **indistinguishable** from a correct one — not "mostly fine", but
10/10 on the full systematic suite, every program, every value.

The drift is one clock per bit against a bit period of 32 clocks; eight clocks of
error at the last bit is still a quarter of a bit time, so every sample lands
inside the right bit. At 16 clocks per bit it does not, and at 8 the receiver
loses the frame entirely.

`ValueError` at `clk_per_bit = 16` is cocotb refusing to convert a read-back byte
that contains `x` bits.

## The `PING` trap

At `clk_per_bit = 16`, `PING` still answers `0xAA` **over a link that cannot carry
data.** `PING` sends `0xF0`, whose bit 7 is already 1; a receiver that samples
bit 7 one bit-time late reads the stop bit, which is also 1, and the command
decodes perfectly. The health check passes and the link is broken.

## What it teaches

Two lessons, and they are why this one is the capstone:

1. **A parametric design needs its parameter swept, not sampled at the default.**
   `clk_per_bit` is set by eight external pins. Testing one value tests one chip.
2. **A link test can pass over a broken link.** `PING → 0xAA` proves that one
   specific byte survived in each direction. It does not prove the link works,
   and the difference between those two statements is a real bug hiding in the
   gap.

## The fix

Restore `if (clkCount < clk_per_bit - 1) begin`.
