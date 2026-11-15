# Lab 01: The adder you already trust

Writeup: [`docs/labs/lab-01-the-adder-you-already-trust-overview.md`](../../docs/labs/lab-01-the-adder-you-already-trust-overview.md)
· live: <https://uoftasic.com/dd104/labs/lab-01-the-adder-you-already-trust-overview.html>

The 4-bit ripple-carry adder from DD102 with a cocotb testbench around it, and a second copy of
the adder that is deliberately broken.

```bash
cd labs/lab-01-the-adder-you-already-trust
make
```

Runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) with no environment setup. It takes about 5 seconds and, on the shipped testbench, ends on
`VERDICT: FAIL`, followed by `make: *** [Makefile:49: check] Error 1`. Both are expected: a failed
verdict exits non-zero on purpose.

## Targets

| Target | What it does |
|---|---|
| `make` | `sim`, then `check` |
| `make sim` | your testbench against `src/`, the good adder |
| `make broken` | your testbench against `broken/`, the adder that drops its carry-in |
| `make check` | the verdict: must PASS on `src/` and FAIL on `broken/` |
| `make clean` | remove `build/` |

`make check TB=test_mine` runs a different module. `TB` names a Python module, not a file:
`TB=test_mine`, not `TB=test_mine.py`.

## Files

| File | What it is |
|---|---|
| `test_adder.py` | the file you edit: two tests, both passing, and one TODO |
| `src/ripple4.sv`, `src/fulladder.sv` | the adder, correct; the same source as DD103 Lab 01 |
| `broken/ripple4.sv` | the same adder with the carry-in dropped; its header says so, and you may read it |
| `check.py` | the verdict, about 150 lines; every later lab uses a bigger version of it |
| `coverage/` | an add-on that runs toggle coverage on the same stimulus, with its own `README.md` and `make` |
| `solutions/` | a reference solution; open it after your own verdict says PASS |

## Done

`make check` says `VERDICT: PASS`. That requires all 512 vectors on both adders, and a failure on
`broken/` that is a count rather than the first bad vector.
