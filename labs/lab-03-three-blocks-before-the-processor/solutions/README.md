# Lab 03 — reference solutions

**Do not read these first.** Get `make check-alu-bugs` to say `3 of 3` and `make rf` to run
five tests, then compare.

```bash
cp solutions/test_alu.py test_alu_solution.py
make check-alu-bugs TB_ALU=test_alu_solution

cp solutions/test_rf.py test_rf_solution.py
make rf TB_RF=test_rf_solution
```

## `test_alu.py` — one change, two buckets

The exhaustive sweep now compares the flags as well as the value, and keeps the two kinds of
mismatch in **separate lists**. That separation is the whole difference between "the ALU is
broken" and "the Z flag is broken":

```
393216 vectors checked -- 0 value mismatches , 25726 flag mismatches
{'ADD': 3840, 'SUB': 3840, 'OR': 255, 'NAND': 255, 'SHL': 14400, 'SHR': 3136}
```

All seven of those numbers are golden, and they factor into sentences:

- **ADD 3840** = 15 × 256. Fifteen non-zero results whose low nibble is zero (`0x10`, `0x20`,
  … `0xF0`), times the 256 operand pairs that produce each one.
- **OR 255**. `A[3:0] == B[3:0] == 0` is 16 × 16 = 256 pairs, minus the one genuinely-zero case
  that a low-nibble detector gets right by accident.
- **0 value mismatches everywhere.** A testbench that checks results and not flags gets a clean
  sweep of all 393,216 vectors on this core.

## `test_rf.py` — the three tests, and the one that matters

t03 is the one to have written yourself: **r0 is an ordinary register on this machine.** It is
not hardwired to zero. RISC-V's `x0` is, MIPS's `$zero` is, and assuming it here is completely
reasonable and completely wrong. Two writes, not one, because a file that latched the first
write and stuck would pass a single-write version.

t04 and t05 are the shapes that recur everywhere: *one write moves one register*, and *an
enable that is not enabling anything*. t05 runs for four cycles rather than one, because "it
did not write on the first edge" and "it does not write" are different claims and only the
second is the requirement.

## The argument to have

`test_pc.py` ships complete and covers `program_counter` exhaustively in four tests, and after
this file `register_file` is covered exhaustively too. That is two modules that are *finished*.
You will very rarely be able to say that about a design, and it is the entire reason unit
testing is worth the setup cost: a small block can be finished, and a 1,178-line processor
cannot.
