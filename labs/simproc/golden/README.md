# SimProc — the correct core

This is the reference copy: SimProc as its authors wrote it, forked at
`1d97772`, with no bugs injected. See `../FORKED-FROM` for the commit, the blob
hashes, and the only two lines this fork changed (both comments).

**This is not a lab package.** If you are looking for the core with a bug in it,
that came from `apply.sh bug-NN`.

```bash
cd test && make -B          # the testbench that shipped with the chip
```

That run passes. It also passes on all thirteen deliberately broken versions of
this core, which is the reason DD104 exists.

## The pin map

`src/tt_um_ieeeuoftasic_simproc.sv` is the whole interface:

| Pin | Meaning |
|---|---|
| `ui_in[0]` | UART RX — every command the chip takes arrives here |
| `uo_out[0]` | UART TX — every reply leaves here |
| `uo_out[1]` | `halt` — the core is in IDLE |
| `uo_out[2]` | `done` — one-cycle pulse, one per retired instruction |
| `uio_in[7:0]` | `clk_per_bit = uio_in × 4` — the UART bit period, in clocks |
| `rst_n` | reset, **active low** at the pin; active-high synchronous inside |

`ena` is ignored. `uio_out` and `uio_oe` are tied to 0 — every bidirectional pin
is an input.
