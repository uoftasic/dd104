# `verify/`: measuring how the bugs behave

Instructor-side. Nothing in here goes to a student.

Every claim in `../README.md` and `../solutions/*.md` (which tests catch a bug, which
numbers a student will see, which bugs the shipped test still passes) came from runs in
this directory on `hpretl/iic-osic-tools:2026.08` (Icarus 14.0, cocotb 2.0.1), not from
reading the RTL.

## Files

| File | What it does |
|---|---|
| `bugs.py` | The catalogue: line, exact old text and new text, per bug. The old text is an anchor: if upstream edits that line, generation stops and names it. |
| `make_patches.py` | Regenerates `../variants/*/bug.patch` from `../golden/` + `bugs.py`. `--check` fails if any patch is stale. |
| `run_verification.py` | The gate. Builds every variant with `apply.sh` and answers the three questions below. Writes `results.json`. |
| `test_suite.py` | The 10-test systematic suite. Passes 10/10 on the clean core. |
| `test_baud.py` | The baud sweep: PING and a byte round trip at seven bit periods. |
| `test_symptoms.py` | One tiny program per variant. This is where the numbers in the student-facing READMEs come from. |
| `test_alu.py` + `Makefile.alu` | The ALU on its own: 393,216 vectors in ~19 s, no processor around it. Clean core: 0 mismatches. |
| `simproc.py` | Assembler + UART bus-functional model, driving the real pins. |
| `golden.py` | The ISA model the suite scores against. |
| `run_symptoms.sh` | Runs `test_symptoms.py` on the clean core and every variant, side by side. |

## The three questions

For each variant `run_verification.py` asks:

1. Does it still compile? Icarus builds the chip's own testbench.
2. Does `test/test.py` still pass? The TinyTapeout boilerplate, untouched.
   A bug that trips it is not hidden and must not ship; the driver prints
   `DROP:` and exits non-zero.
3. Does a real test catch it? The suite at `clk_per_bit = 32` (the lab
   default), the same suite at `clk_per_bit = 8`, and the baud sweep. A bug
   nothing catches is also a `DROP:`, because it is not teaching what you think.

```bash
cd labs/simproc
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" -v /tmp/simproc-verify:/scratch -w /work \
  hpretl/iic-osic-tools:2026.08 --skip bash -c \
  'python3 /work/verify/run_verification.py --work /scratch'
```

`--quick` skips the baud sweep (the slowest step at about 15 s a variant);
`--only bug-07,bug-11` checks a subset; `--alu` adds the 393,216-vector ALU sweep
(about 19 s a variant, and only bug-01, bug-02 and bug-03 are visible to it).

The ALU sweep on its own, against any working copy:

```bash
cd <workdir>/verify && make -f Makefile.alu -B
```

Run that one by hand at least once. It finds three of the thirteen bugs without
knowing that a processor exists, and it does not find bug-06, which is the cleanest
demonstration in the course of where a unit test stops.

## A baud-dependent testbench bug

The suite's `run_and_compare` used to end each program with a UART `HALT`. At
`clk_per_bit = 8` that is harmless. At `clk_per_bit = 32` a three-byte command
takes 1,056 clocks to shift in, and the core keeps executing the whole time.
Past the end of a short program it runs unimplemented opcodes at 4 cycles each,
and the PC is 8 bits wide against a 64-byte RAM, so it wraps to 0 and runs the
program a second time, over its own results.

Measured, on the clean core: 10/10 at `clk_per_bit = 8`, and 8/10 at
`clk_per_bit = 32`, with T01 and T06 failing on a processor with nothing wrong
with it. The suite was baud-dependent and nobody had run it at another baud.

The fix is `SimProcBus.stop()`: pulse `rst_n` for 4 clocks. The RAM has no
reset, so the program and its results survive; the core stops in 6 clocks
instead of 1,056. After it, the clean core is 10/10 at both settings.

It would make a good lab: a testbench bug that only exists at one parameter value,
in a harness written to prove that designs need their parameters swept.
