# Lab 05: Every answer is right

Writeup: [`docs/labs/lab-05-every-answer-is-right-overview.md`](../../docs/labs/lab-05-every-answer-is-right-overview.md)
· live: <https://uoftasic.com/dd104/labs/lab-05-every-answer-is-right-overview.html>

Two broken processors whose every register, flag, PC value and byte of memory is correct, and the
checks on `done`, `halt` and the cycle count that catch them.

```bash
cd labs/lab-05-every-answer-is-right
make blind       # start here: a complete architectural suite misses both
make new
make hunt
make probe       # the same run, with the simulator's output shown
make verdict
```

Runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) with no environment setup. The Makefile includes `../common/lab.mk`, so you need the whole
repository.

## Targets

| Target | What it does |
|---|---|
| `make blind` | `test_architecture.py` against the golden core and both bugs in the pool |
| `make new` | deal a mystery core into `core/` |
| `make hunt` | your testbench against `core/`, summary only |
| `make probe` | the same run with the simulator's own output shown live; `make hunt VERBOSE=1` is the same, and `make verdict VERBOSE=1` does it for all three rows (see [Lab 04's README](../lab-04-your-first-bug-hunt/README.md)) |
| `make verdict` | the three-row grade, as in Lab 04 |
| `make reveal` | give up |
| `make sim` | your testbench against the golden core |
| `make check BUG=B08` | the two-sided check against a named bug |
| `make clean` | remove `build/`; leaves `core/` alone |

The pool is `B08` and `B13`.

## Files

| File | What it is |
|---|---|
| `test_lab05.py` | the file you edit: two tests and a TODO list |
| `test_architecture.py` | Lab 04's finished suite with its cycle-count assertion removed, used by `make blind`; do not edit it |
| `blind.py` | runs `test_architecture.py` against both bugs in the pool |
| `hunt.py` | the Lab 04 dealer and grader, with a two-bug pool |
| `solutions/` | four tests that catch both; open them after your own verdict passes |

## Done

`make verdict` says `VERDICT: PASS` on the core you were dealt, and ideally on both.
