# Lab 03 — Three blocks before the processor

Writeup: [`docs/labs/lab-03-three-blocks-before-the-processor-overview.md`](../../docs/labs/lab-03-three-blocks-before-the-processor-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-03-three-blocks-before-the-processor>

SimProc is 1,178 lines. Three of its modules are 16, 31 and 34 lines, and cocotb can elaborate
any one of them on its own as the top level. Two of the three can be *finished* — tested until
there is no behaviour left in them that is untested — and the third can be driven
exhaustively, all 393,216 vectors, in about twenty seconds.

```bash
cd labs/lab-03-three-blocks-before-the-processor
make
```

Inside the workbench container (`hpretl/iic-osic-tools:2026.04` — cocotb 2.0.1, Icarus
Verilog 14.0). No environment setup. Includes `../common/lab.mk`'s sibling `sim.mk`, so you
need the repository, not just this directory.

## Targets

| | | wall clock |
|---|---|---|
| `make` | `pc`, `rf`, `alu`, then the verdict | ~60 s |
| `make pc` | `test_pc.py` against `program_counter` (16 lines of RTL) | ~3 s |
| `make rf` | `test_rf.py` against `register_file` (31 lines) | ~1.5 s |
| `make alu` | `test_alu.py` against `ALU` (34 lines, 393,216 vectors) | ~23 s |
| `make check` | the verdict: `test_alu` passes the golden ALU, FAILS on `BUG` (default `B01`) | ~45 s |
| `make check BUG=B03` | pick a different broken ALU | |
| `make check-alu-bugs` | all three ALU bugs at once | ~90 s |
| `make clean` | remove `build/` | |

`TB_PC`, `TB_RF` and `TB_ALU` override which module runs against which block.

## Files

| | |
|---|---|
| `test_pc.py` | **ships complete.** Four tests, and after them `program_counter` has no untested behaviour. Read it as the model for the other two. |
| `test_rf.py` | **ships with two tests and three TODOs.** t03 finds an architectural fact you will use in every later lab. |
| `test_alu.py` | **ships with three tests and one TODO.** t02 is exhaustive on values; the TODO is the flags. |
| `check.py` | the unit-level verdict. Imports the same bug catalogue the processor-level labs use. |
| `solutions/` | reference solutions for `test_alu.py` and `test_rf.py`. Not before your own run. |

The RTL is `../common/rtl/simproc_system.sv` — the whole 1,178-line file, compiled every time.
cocotb elaborates one module from it as the top level and the other 1,100 lines are simply not
connected to anything.

## Golden numbers

`make alu` on the clean ALU:

```
393216 vectors checked, 0 value mismatches
** test_alu.t02_every_vector_the_alu_can_be_given   PASS      393216.00 **
** TESTS=3 PASS=3 FAIL=0 SKIP=0                               393224.00 **
```

**393,216 vectors, 0 mismatches, 393,224.00 ns** — all golden. Six operations × 256 × 256.
About 20 s of wall clock, which is BALLPARK.

`make check-alu-bugs` on the shipped `test_alu.py`:

```
  caught  B01_sub_operands_swapped           3 tests, 2 FAILED
  caught  B02_nand_is_nor                    3 tests, 2 FAILED
  MISSED  B03_zero_flag_low_nibble           3 tests, all passed
------------------------------------------------------------------------
 2 of 3 ALU bugs caught.
```

and once the flag TODO is done, `3 of 3`. The counts each bug produces are golden and each one
factors into a sentence about the bug:

| | value mismatches | flag mismatches |
|---|---|---|
| B01 | `{'SUB': 65024}` | 0 |
| B02 | `{'NAND': 65280}` | 0 |
| B03 | **0** | `{'ADD': 3840, 'SUB': 3840, 'OR': 255, 'NAND': 255, 'SHL': 14400, 'SHR': 3136}` — 25,726 total |

## Definition of done

`make check-alu-bugs` says `3 of 3 ALU bugs caught`, and `make rf` runs five tests instead of
two.
