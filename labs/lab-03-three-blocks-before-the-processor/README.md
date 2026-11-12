# Lab 03: Three blocks before the processor

Writeup: [`docs/labs/lab-03-three-blocks-before-the-processor-overview.md`](../../docs/labs/lab-03-three-blocks-before-the-processor-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-03-three-blocks-before-the-processor-overview>

Unit tests for three SimProc modules, each elaborated on its own as the simulation top level:
`program_counter` (16 lines of RTL), `register_file` (31) and `ALU` (34, driven with all 393,216
legal vectors).

```bash
cd labs/lab-03-three-blocks-before-the-processor
make
```

Runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) with no environment setup. It uses `../common/sim.mk` and the RTL in `../common/rtl/`, so
you need the whole repository, not just this directory.

## Targets

| Target | What it does | Wall clock |
|---|---|---|
| `make` | `pc`, `rf`, `alu`, then the verdict | ~60 s |
| `make pc` | `test_pc.py` against `program_counter` | ~3 s |
| `make rf` | `test_rf.py` against `register_file` | ~1.5 s |
| `make alu` | `test_alu.py` against `ALU`, all 393,216 vectors | ~23 s |
| `make check` | the verdict: `test_alu` passes the golden ALU and FAILS on `BUG` (default `B01`) | ~45 s |
| `make check BUG=B03` | the same, against a different broken ALU | |
| `make check-alu-bugs` | all three ALU bugs at once | ~90 s |
| `make clean` | remove `build/` | |

`TB_PC`, `TB_RF` and `TB_ALU` choose which module runs against which block.

## Files

| File | What it is |
|---|---|
| `test_pc.py` | ships complete: four tests, after which `program_counter` has no untested behaviour |
| `test_rf.py` | ships with two tests and three TODOs |
| `test_alu.py` | ships with three tests and one TODO (the flags) |
| `check.py` | the unit-level verdict; it uses the same bug catalogue as the processor-level labs |
| `solutions/` | reference `test_alu.py` and `test_rf.py`; open them after your own run passes |

The RTL is the whole 1,178-line `../common/rtl/simproc_system.sv`, compiled every time; cocotb
elaborates one module from it as the top level.

## Done

`make check-alu-bugs` says `3 of 3 ALU bugs caught`, and `make rf` runs five tests instead of two.
If it says `NO COUNT` instead, one of your tests crashed rather than caught anything; the writeup's
Part 6 covers it.
