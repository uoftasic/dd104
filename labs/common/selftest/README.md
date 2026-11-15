# `selftest/`: checking the graders

```bash
cd labs/common
make selftest            # the classifier and the source audit. Under a second.
make selftest FULL=1     # ... and every checker in the course, for real. Minutes.
```

`inject.py` states the principle and this directory enforces it:

> A grader that says PASS when it did nothing is worse than no grader at all.

DD104 shipped two graders that did exactly that, and students found both:

| what the student did | what the grader said | what was true |
|---|---|---|
| a `test_alu.py` whose failure path raised `NameError` | `3 of 3 ALU bugs caught` | three crashes, zero catches |
| half of Lab 01's TODO | `VERDICT: PASS ... a test worth committing` | the failure was an anecdote, not the count Step 4 is about |

The first is the general case. cocotb writes both "the assertion fired" and
"the test raised `NameError`" into `results.xml` as `<failure>`, so
a checker that reads them the same way counts a testbench that crashed as a
testbench that caught something. `../verdict.py` is the one place that tells
them apart; every checker in the course reads it from there, and Part 3 of
this selftest fails if any of them re-grows its own copy.

## What is in here

Every `tb_*.py` is deliberately broken and is not an example to copy. Each
one names, in its own docstring, the verdict it must provoke.

| fixture | broken how | must provoke |
|---|---|---|
| `tb_adder_blows_up.py` | `NameError` on the first vector of every run | FAIL, naming `NameError` |
| `tb_adder_blows_up_on_failure.py` | correct until it finds a bug, then `NameError` while building the message | FAIL: a crash is not a catch |
| `tb_adder_empty.py` | `pass`: the lazy testbench | FAIL: passes the broken adder too |
| `tb_adder_half_todo.py` | sweeps `cin`, still asserts on the first bad vector | FAIL: the second half of the TODO is not done |
| `tb_alu_blows_up_on_failure.py` | the `3 of 3 ALU bugs caught` testbench, verbatim | FAIL / `NO COUNT` |
| `tb_core_blows_up_on_failure.py` | the same shape at processor level, compared on registers | FAIL, row marked `BROKEN` |
| `tb_core_handshake_blows_up.py` | the same shape again, counting `done` pulses, the only kind that reaches Lab 05's pool | FAIL, row marked `BROKEN` |
| `tb_core_empty.py` | `pass`, at processor level | FAIL: passes the broken core too |

## The four parts

The script runs the fastest parts first, so it prints them in the order 1, 3, 4,
then 2. The numbers below are the labels it prints.

1. The classifier, against hand-written `results.xml`: one file per shape
   cocotb 2.0.1 can produce, including `<skipped/>` and a `<failure>` with no
   `error_type` (which is how cocotb records a test that could not start).
   It needs no simulator and takes under a second.
2. End to end (`FULL=1`): every `check*.py` and `hunt.py` in the course,
   each fed a fixture, each required to print a specific verdict and exit
   non-zero.
3. The source audit: no checker may carry its own `class Result`, its own
   `ET.parse`, or a `findall("error")`. cocotb 2.x never writes an `<error>`
   element, so that last one is dead code that looks like a safety net.
4. The answer key against the catalogue: every
   `../../simproc/solutions/bug-NN.md` must carry the tier `bugs.py` gives that
   bug, and must name the lab that tier is met in. `bugs.py` is what the
   tooling prints (`make bugs`, and the `tier N` on every `check-all` row); the
   solution files are what a student reads when they give up. Six of the
   thirteen once disagreed, because nothing executed those numbers.

A lab with a `core/` directory in it has a hunt in progress. Part 2 skips that
lab instead of dealing it a fresh core, because `make new` would delete `core/`,
and a selftest must not cost you your lab.
