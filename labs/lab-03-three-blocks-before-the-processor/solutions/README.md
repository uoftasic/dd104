# Lab 03: reference solutions

Before you read these, get `make check-alu-bugs` to say `3 of 3` and `make rf` to run five tests.
Then copy each solution next to your own file and run it the same way, so you can compare:

```bash
cp solutions/test_alu.py test_alu_solution.py
make check-alu-bugs TB_ALU=test_alu_solution

cp solutions/test_rf.py test_rf_solution.py
make rf TB_RF=test_rf_solution
```

## `test_alu.py`: one change, two counts

The exhaustive sweep now compares the flags as well as the value, and it keeps the two kinds of
mismatch in separate lists. That separation is what lets the report tell "the ALU is broken" apart
from "the Z flag is broken":

```
393216 vectors checked -- 0 value mismatches , 25726 flag mismatches
{'ADD': 3840, 'SUB': 3840, 'OR': 255, 'NAND': 255, 'SHL': 14400, 'SHR': 3136}
```

All of those numbers are exact, and each one can be explained in a sentence:

- ADD 3840 = 15 × 256: there are fifteen non-zero results whose low nibble is zero (`0x10`,
  `0x20`, … `0xF0`), and 256 operand pairs produce each one.
- OR 255: `A[3:0] == B[3:0] == 0` covers 16 × 16 = 256 pairs, minus the one case where the result
  really is zero, which a low-nibble detector gets right by accident.
- 0 value mismatches everywhere: on this core, a testbench that checks results but not flags gets
  a clean sweep of all 393,216 vectors.

## `test_rf.py`: three tests, one that matters

`t03` is the one you should have written yourself, because `r0` is an ordinary register on this
machine and is not hardwired to zero. RISC-V's `x0` and MIPS's `$zero` are hardwired, so it's
reasonable to assume the same here, but the assumption is wrong. The test uses two writes rather
than one, because a register that latched the first write and then stuck would pass a single-write
version.

`t04` and `t05` check properties you'll test in almost every design: one write changes one
register, and a write enable that isn't asserted writes nothing. `t05` runs for four cycles rather
than one, because "it did not write on the first edge" and "it does not write" are different
claims, and only the second one is the requirement.

## The argument to have

`test_pc.py` ships complete and covers `program_counter` exhaustively in four tests, and with this
file `register_file` is covered exhaustively too. That makes two modules that are finished, which
you will rarely be able to say about a design. It's also why unit testing is worth its setup cost:
a small block can be tested until it's finished, and a 1,178-line processor can't.
