# Lab 05 — Every answer is right and it is still broken

Writeup: [`docs/labs/lab-05-every-answer-is-right-overview.md`](../../docs/labs/lab-05-every-answer-is-right-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-05-every-answer-is-right>

Two broken processors. Every register, every flag, every PC value and every byte of memory
they produce is correct, for every program you can write. The golden model agrees with them
completely. Your Lab 04 suite passes on both.

```bash
cd labs/lab-05-every-answer-is-right
make blind       # start here: watch a complete architectural suite miss both
make new
make hunt
make probe       # the same run, with the simulator's output shown
make verdict
```

Inside the workbench container (`hpretl/iic-osic-tools:2026.08` — cocotb 2.0.1, Icarus
Verilog 14.0). No environment setup. Includes `../common/lab.mk`, so you need the repository.

## `make blind`, which is the whole argument

```
      ok  the golden core                            10 tests, all passed      13.4s
  MISSED  B08                                        10 tests, all passed      13.5s
  MISSED  B13                                        10 tests, all passed      13.4s
------------------------------------------------------------------------
 Three identical green rows. Every architectural result on all three
 of those processors is correct, and two of them are broken.

 What test_architecture.py never reads: the `done` pin, the `halt`
 pin, and the number of clock cycles anything took. Those are the
 three things this lab is about.
```

`test_architecture.py` is Lab 04's finished suite: ten tests covering all four registers, the
PC, both flags and every byte of memory after every instruction; every shift amount; all
sixteen branch displacements; a compare followed by two branches. It catches every bug in Labs
03 and 04. There is nothing wrong with it. It reads architectural state, and neither of these
bugs is in architectural state.

## Targets

| | |
|---|---|
| `make blind` | the demonstration above |
| `make new` | deal a mystery core into `core/` |
| `make hunt` | your testbench against `core/` — summary only |
| `make probe` | the same run, showing the simulator's own output: every `print()`, every `dut._log` line, live. `make hunt VERBOSE=1` is the same thing, and `make verdict VERBOSE=1` does it for all three rows. See [Lab 04's README](../lab-04-your-first-bug-hunt/README.md#seeing-your-own-output--make-probe). |
| `make verdict` | the three-row grade (see [Lab 04's README](../lab-04-your-first-bug-hunt/README.md)) |
| `make reveal` | give up |
| `make sim` | your testbench against the golden core |
| `make check BUG=B08` | the two-sided check against a named bug |
| `make clean` | remove `build/`; leaves `core/` alone |

## Files

| | |
|---|---|
| `test_lab05.py` | **the file you edit.** Two tests and a TODO list. |
| `test_architecture.py` | Lab 04's finished suite, used by `make blind`. Do not edit it. |
| `blind.py` | runs `test_architecture.py` against both bugs in the pool. |
| `hunt.py` | the same dealer and grader as Lab 04, with a two-bug pool. |
| `solutions/` | four tests that catch both. Not before your own verdict. |

## Golden numbers

The program every test in this file uses is nine instructions, one of them a `STORE`, and its
cost is arithmetic rather than measurement:

```
SUB 4 + ORI 5 + SHL 4 + SUB 4 + ADD 4 + SUB 4 + ORI 5 + ADD 4 + STORE 3 = 37
```

| | golden | `B08` | `B13` |
|---|---|---|---|
| `done` pulses over the program | **9** | **8** | 9 |
| `halt` high, of the running cycles | **0** | 0 | **1** |
| clock cycles, `sp.run()` | **37** | 37 | **38** |
| every register, flag, byte of memory | correct | correct | correct |

All twelve of those numbers are golden. Three of them are wrong and nine of them are not, and
the three that are wrong are the entire observable difference between a working processor and
one that would ship.

## The sentence this lab exists for

If your scoreboard triggers on `done`, `B08` does not make your test FAIL. It makes your test
**silently stop scoring** — the trigger never fires, so the comparison never runs, so there is
nothing to report, so the run is green. `make sim` on the shipped `test_lab05.py` prints:

```
a done-triggered scoreboard would have made 9 comparisons for a 9-instruction program
```

On `B08` the same line says 8. Nothing goes red. That is the failure mode.

## Definition of done

`make verdict` says `VERDICT: PASS` on the core you were dealt — and ideally on both, since
there are only two.
