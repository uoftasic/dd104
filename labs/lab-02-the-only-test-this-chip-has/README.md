# Lab 02: The only test this chip has

Writeup: [`docs/labs/lab-02-the-only-test-this-chip-has-overview.md`](../../docs/labs/lab-02-the-only-test-this-chip-has-overview.md)
· live: <https://uoftasic.com/dd104/labs/lab-02-the-only-test-this-chip-has-overview.html>

You run SimProc's one shipped test against the good core and all thirteen broken ones, and then
write a testbench of your own that catches `B01`.

```bash
cd labs/lab-02-the-only-test-this-chip-has
make shuttle     # start here
make             # sim, then check
```

Everything runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) with no environment setup. The Makefile includes `../common/lab.mk`, so you need the whole
repository, not just this directory.

## Targets

All of these come from [`../common/lab.mk`](../common/lab.mk), which every SimProc lab includes.

| Target | What it does | Wall clock |
|---|---|---|
| `make shuttle` | the shipped test against the golden core and all thirteen broken ones | ~24 s |
| `make` | `sim`, then `check` | ~8 s |
| `make sim` | your testbench against the golden core | ~4 s |
| `make check` | the verdict: PASS on golden, FAIL on `BUG` (default `B01`) | ~4 s |
| `make check BUG=B06` | the same, against a different broken core | |
| `make check-all` | your testbench against all thirteen | ~22 s |
| `make waves` | the `sim` run, dumping `waves.vcd` | ~2 s |
| `make bugs` | the catalogue: names, tiers, and what each one teaches | instant |
| `make model` | the golden model, with no simulator | instant |
| `make clean` | remove `build/`, `waves.vcd`, `__pycache__` | |

The wall-clock times are ballpark figures. To run a different testbench, set `TB`, as in
`TB=test_mine`; it names a Python module, not a file.

## Files

| File | What it is |
|---|---|
| `test_lab02.py` | the file you edit: three tests, all passing, and one TODO |
| `solutions/` | a reference solution; open it after your own verdict says PASS |

The harness, assembler, golden model, bug catalogue and RTL are in
[`../common/`](../common/README.md). The docstring at the top of `test_lab02.py` covers what this
lab needs from them.
