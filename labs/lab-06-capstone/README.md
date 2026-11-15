# Lab 06: Capstone

Writeup: [`docs/labs/lab-06-capstone-overview.md`](../../docs/labs/lab-06-capstone-overview.md)
· live: <https://uoftasic.com/dd104/labs/lab-06-capstone-overview.html>

This lab deals you one of the three tier-5 bugs, which are the hardest in the catalogue to think
of. It also holds the course deliverable: a test suite of your own that catches all thirteen bugs,
plus a written bug report for one of the three.

```bash
cd labs/lab-06-capstone
make new           # one of the three
make hunt
make probe         # the same run, with the simulator's output shown
make verdict
make check-all     # the deliverable: your suite against all thirteen
```

It runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) and needs no environment setup. The Makefile includes `../common/lab.mk`, so you need the whole
repository. `make check-all` takes about 4 min 35 s on the reference suite (fourteen full builds
and simulations).

## Targets

| Target | What it does |
|---|---|
| `make new` | deal one of `B10`, `B11`, `B12` into `core/` |
| `make hunt` | your suite against `core/`, summary only |
| `make probe` | the same run with the simulator's own output shown live; `make hunt VERBOSE=1` is the same, and `make verdict VERBOSE=1` does it for all three rows (see [Lab 04's README](../lab-04-your-first-bug-hunt/README.md)) |
| `make verdict` | the three-row grade, as in Lab 04 |
| `make reveal` | give up |
| `make check-all` | your suite against all thirteen |
| `make sim` | your suite against the golden core |
| `make check BUG=B11` | one named bug |
| `make bugs` | the catalogue: names and tiers |
| `make clean` | remove `build/`; leaves `core/` alone |

## Files

| File | What it is |
|---|---|
| `test_capstone.py` | the file you edit: one test, a description of the three bugs that gives none of them away, and a coverage list; start by bringing in your Lab 04 and Lab 05 tests |
| `BUG-REPORT-template.md` | the five parts of a report a designer can act on; copy it to `BUG-REPORT.md` |
| `BUG-REPORT-EXAMPLE.md` | the template filled in for `B01`, which is not in this pool |
| `hunt.py` | the dealer and grader, with a three-bug pool |
| `solutions/` | a sixteen-test suite that catches all thirteen; open it after your own `13 of 13` |

## Done

`make check-all` says `13 of 13 caught`, and `BUG-REPORT.md` exists and has all five parts.
