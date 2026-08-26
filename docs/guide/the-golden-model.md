# The golden model

**Question this page answers:** *The input space is too big to walk. What do I compare against instead?*

> **This page has not been written yet.** It is on the DD104 outline and it has an author.
> Until it lands, the material it will cover is in
> [`labs/common`](https://github.com/uoftasic/dd104/tree/main/labs/common) — the package runs
> today with `make` alone.
>
> Something you needed and could not find? Say so in the
> [team Discord](https://discord.gg/hrJnP5UsGz).

<!-- ===================================================================
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    The input space is too big to walk. What do I compare against instead?

What this page must contain:
  - The idea: a second, independent implementation of the SPECIFICATION,
    written in a language where it is easy to be obviously right. About 120
    lines of Python is enough for this whole ISA - labs/common/golden.py.
  - Independence is the whole value. Two implementations sharing a
    misunderstanding agree perfectly and both are wrong. Say plainly what
    the golden model does NOT protect you from.
  - Run it with no simulator at all: `make model` (MEASURED, re-run):
        16 instructions in memory, 28 executed, 109 clock cycles
        registers: r0=32 r1=15 r2=1 r3=32
        mem[0x20] = 15   (all 28 instructions executed)
  - PREDICT -> BE WRONG -> WATCH THE ARITHMETIC CLOSE. Hand-count the
    cycles of the sum-of-1-to-5 program and close it to the cycle:
    30 + (4+4+3)x5 + 24 = 109. If the hardware says 114 instead, something
    takes one extra cycle five times - once per loop iteration - and that
    is a whole diagnosis from one integer.
  - Instruction-by-instruction comparison: `await trace(sp, n, model=g)`
    steps both and names the FIRST disagreement. Show the real message:
        AssertionError: instruction 19, at address 19 (0x66 = SUB r1, r2),
        left the machine in a ...
    First disagreement, not last - explain why that distinction is the
    difference between a five-minute and a two-hour debug.
  - The model is also a program generator's oracle: random programs are
    only useful because something knows the right answer. Bridge to
    directed-random-and-the-gap.md.
  - Reflex rule.
  - Forward to: flags-are-state.md

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
=================================================================== -->
