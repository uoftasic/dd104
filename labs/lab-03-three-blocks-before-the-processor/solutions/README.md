# Lab 03: reference solutions

Get `make check-alu-bugs` to say `3 of 3` and `make rf` to run five tests before you read these,
then compare.

```bash
cp solutions/test_alu.py test_alu_solution.py
make check-alu-bugs TB_ALU=test_alu_solution

cp solutions/test_rf.py test_rf_solution.py
make rf TB_RF=test_rf_solution
```

## `test_alu.py`: one change, two counts

The exhaustive sweep now compares the flags as well as the value, and keeps the two kinds of
mismatch in separate lists. That separation is the difference between "the ALU is broken" and
"the Z flag is broken":

```
393216 vectors checked -- 0 value mismatches , 25726 flag mismatches
{'ADD': 3840, 'SUB': 3840, 'OR': 255, 'NAND': 255, 'SHL': 14400, 'SHR': 3136}
```

All of those numbers are exact, and they factor into sentences:

- ADD 3840 = 15 × 256: fifteen non-zero results whose low nibble is zero (`0x10`, `0x20`, …
  `0xF0`), times the 256 operand pairs that produce each one.
- OR 255: `A[3:0] == B[3:0] == 0` is 16 × 16 = 256 pairs, minus the one genuinely zero case that
  a low-nibble detector gets right by accident.
- 0 value mismatches everywhere: a testbench that checks results and not flags gets a clean sweep
  of all 393,216 vectors on this core.

## `test_rf.py`: three tests, one that matters

`t03` is the one to have written yourself: `r0` is an ordinary register on this machine, not
hardwired to zero. RISC-V's `x0` is hardwired and MIPS's `$zero` is, and assuming the same here is
reasonable and wrong. It uses two writes, not one, because a register that latched the first write
and stuck would pass a single-write version.

`t04` and `t05` are shapes that recur everywhere: one write moves one register, and an enable that
is not enabled writes nothing. `t05` runs for four cycles rather than one, because "it did not
write on the first edge" and "it does not write" are different claims and only the second is the
requirement.

## The argument to have

`test_pc.py` ships complete and covers `program_counter` exhaustively in four tests, and with this
file `register_file` is covered exhaustively too. That is two modules that are finished. You will
rarely be able to say that about a design, and it is why unit testing is worth its setup cost: a
small block can be finished, and a 1,178-line processor cannot.
