# Lab 04: Your first bug hunt

Writeup: [`docs/labs/lab-04-your-first-bug-hunt-overview.md`](../../docs/labs/lab-04-your-first-bug-hunt-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-04-your-first-bug-hunt-overview>

A processor with one line changed, a five-bug pool, and a three-row grade that requires a test
which fails on the core you were dealt.

```bash
cd labs/lab-04-your-first-bug-hunt
make new         # deal a mystery core into core/
make hunt        # your testbench against it
make probe       # the same run, showing everything the simulator prints
make verdict     # the grade
```

Runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) with no environment setup. The Makefile includes `../common/lab.mk`, so you need the whole
repository, not just this directory.

## Targets

| Target | What it does |
|---|---|
| `make new` | deal a mystery core into `core/`; this deletes any `core/` you have |
| `make new BUGPICK=B06` | deal a specific bug |
| `make hunt` | your testbench against `core/`, summary only |
| `make probe` | the same run with the simulator's own output shown live, plus the `make -f sim.mk` command it ran |
| `make probe TB=test_probe` | probe a scratch file instead of `test_lab04.py` |
| `make hunt VERBOSE=1` | the same as `make probe` |
| `make verdict` | the three-row grade: golden PASS, dealt core FAIL, `core/` PASS |
| `make verdict VERBOSE=1` | the grade, with full output for each row |
| `make reveal` | give up; it tells you the bug's name and what it hides behind, not the line |
| `make sim` | your testbench against the golden core |
| `make check BUG=B05` | the two-sided check against a named bug |
| `make check-all` | your testbench against all thirteen |
| `make waves` | the `sim` run, dumping `waves.vcd` |
| `make bugs` | the catalogue: names and tiers |
| `make clean` | remove `build/`; it leaves `core/` alone, so it cannot lose your hunt |

The pool is `B04`, `B05`, `B06`, `B07` and `B09`. The grade only ever runs `TB=test_lab04`.

## Files

| File | What it is |
|---|---|
| `test_lab04.py` | the file you edit: four tests, all passing, and a TODO list |
| `test_probe.py` | scratch space for probe programs; `make probe TB=test_probe`; never graded |
| `hunt.py` | deals a core, seals which one it was, and runs the grade |
| `core/` | created by `make new`; the RTL you edit; gitignored |
| `solutions/` | a ten-test suite that catches all five; open it after your own verdict passes |

`core/.sealed` holds the answer, base64-encoded. Decoding it costs you the lab. `make reveal` does
it for you and says so.

## Done

`make verdict` says `VERDICT: PASS`, three green rows, on the core you were dealt.
