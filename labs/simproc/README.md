# `labs/simproc/`: the core and its thirteen bug variants

This is DD104's copy of SimProc, an 8-bit processor a student team designed and taped
out, forked at a pinned commit, plus thirteen deliberate bugs that hide inside it.

This directory is not a lab; it is where lab cores are made. A lab package is one buggy
core, produced from here by `apply.sh`, with nothing in it that gives the answer away.

```bash
./apply.sh bug-07 /tmp/lab2-core      # one buggy core, ready to simulate
./apply.sh golden /tmp/clean-core     # the correct core, for reference
```

## What is here

| Path | What it is | Copied into a package by `apply.sh`? |
|---|---|---|
| `golden/src/` | The correct RTL. 1178 lines, forked at `1d97772`. | No |
| `golden/test/` | The testbench that shipped with the chip, verbatim. | Yes |
| `variants/bug-NN/bug.patch` | One bug, as a unified diff against `golden/`. | No |
| `variants/bug-NN/README.md` | What the student is told: the symptom, and only the symptom. | Yes, as the package README |
| `solutions/bug-NN.md` | What the bug actually is, why it hides, and what it teaches. | No |
| `verify/` | The harness that proved every claim on this page. | No |
| `FORKED-FROM` | Upstream commit, blob hashes, and the two comments we changed. | — |

`apply.sh` copies `src/`, `test/`, the variant README and a one-line `VARIANT`
stamp. It never copies `golden/`, the patch, `solutions/` or `verify/`, so a directory
built by `apply.sh` can be handed to a student as-is.

> This is about what a package contains, not what is on a student's disk.
> `uoftasic/dd104` is a public repository, so `golden/`, `variants/*/bug.patch`,
> `solutions/` and `labs/common/bugs.py` are in every clone. The course says so (see
> *Requests to avoid* in
> [Getting started](https://uoftasic.com/dd104/#/guide/getting-started)) and asks students
> not to read them. Nothing here is secret; it is an honour system with the files named.

## The bugs

Thirteen, one patch each, `bug-01` to `bug-13`. They map one-to-one onto the
catalogue names `B01` to `B13`: `bug-07` is `B07`.

| | Variant | Caught by | Hidden because |
|---|---|---|---|
| Tier 1 — the ALU, on its own (Lab 03) | `bug-01` | ALU sweep, T01, T08 | `A-B == B-A` on 512 of 65,536 vectors, and `SUB rX,rX` is one of them |
| | `bug-02` | ALU sweep, T01, T08 | `NAND rX,rX` is how you write NOT, and NOR agrees with NAND on exactly those 256 vectors |
| | `bug-03` | ALU sweep (flags only), T03, T06, T10 | every value is right; only N and Z are wrong, and 600 random instructions miss it |
| Tier 2 — decode and the register file (Lab 04) | `bug-04` | 7 of 10 | invisible whenever rA == rB |
| | `bug-06` | T03, T08 — not the ALU sweep | shift by 0 and 1 are correct, and 1 is what everyone writes |
| | `bug-07` | T10 only | `LOAD r1,r1` is a real idiom and is correct under the bug |
| Tier 3 — control flow (Lab 04) | `bug-05` | T04, T07, T08 | every forward branch is exactly right |
| | `bug-09` | T05, T08 | one branch after a compare works perfectly; two do not |
| Tier 4 — protocol, not data (Lab 05) | `bug-08` | T09 only | every architectural result is correct |
| | `bug-13` | T07 only | functionally identical output, one wasted cycle |
| Tier 5 — the hard end (Lab 06) | `bug-10` | T02, T03, T08 | `0 \| imm == 0 + imm`, so the first ORI after reset is always right |
| | `bug-11` | 7 of 10 | after reset both registers hold 0, so the first ORI looks correct |
| | `bug-12` | the baud sweep only | invisible at the default baud; `PING` still answers `0xAA` over a link that cannot carry data |

The "caught by" column is measured: `verify/results.json` is the run that produced
it, and `verify/README.md` explains how to reproduce it. (T01–T10 are the tests of the
10-test systematic suite in `verify/test_suite.py`, not the lab or reference suites.)

## All thirteen pass the shipped test

The only test SimProc has ever had passes on a processor whose `SUB` is backwards.

`golden/test/test.py` is the untouched TinyTapeout template. It sets `ui_in=1`,
waits 100 clocks, and asserts `uo_out == 3`. Decoded through the pin map that is
`uart_tx=1` (line idle), `halt=1` (core in IDLE) and `done=0`: it asserts that the
processor is not running. It sends no command, loads no program and executes no
instruction.

All 13 variants pass it, checked on every release.

## Verifying the whole set

Runs in the workbench, `hpretl/iic-osic-tools:2026.08` (Icarus 14.0, cocotb 2.0.1):

```bash
cd labs/simproc
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" -v /tmp/simproc-verify:/scratch -w /work \
  hpretl/iic-osic-tools:2026.08 --skip bash -c \
  'python3 /work/verify/run_verification.py --work /scratch'
```

For each variant it builds a working copy with `apply.sh` and answers three
questions without reading the source:

1. Does it still compile? Icarus builds the chip's own testbench.
2. Does the shipped test still pass? If a bug fails `test/test.py` it is not
   hidden, and it does not ship.
3. Does a real test catch it? The 10-test systematic suite at the lab's
   default `clk_per_bit`, the same suite at `clk_per_bit = 8`, and a baud sweep.

Roughly 28 s per variant, about 6.5 minutes for the set.

## Adding a bug

1. Add an entry to `verify/bugs.py` with the exact current text of the line
   you are changing. That text is the anchor: if upstream ever edits that line,
   patch generation stops and names it, instead of silently making a different
   bug.
2. `python3 verify/make_patches.py`
3. Write `variants/bug-NN/README.md`: the symptom only. Never the file, the line
   or the cause.
4. Write `solutions/bug-NN.md`: everything else.
5. Re-run the verification. If nothing catches the bug, or if the boilerplate
   test catches it, drop the bug. Both failures mean it is not teaching what you
   think it is.

## Licence

The RTL under `golden/src/` and the testbench under `golden/test/` are
Apache-2.0, upstream's licence, kept as `LICENSE.upstream`. Everything DD104
wrote around them (the patches, the READMEs, the harness) is MIT, like the rest
of this repo.
