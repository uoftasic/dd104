# Output that is not an error

**Question this page answers:** *The screen is full of red and yellow. Did something break?*

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
    The screen is full of red and yellow. Did something break?

What this page must contain:
  The page a student lands on at 2 a.m. Every entry: the exact text, what
  produced it, whether it matters, and the one-line rule for telling it
  apart from a real failure.
  - Icarus `sorry: constant selects in always_* processes are not fully
    supported` - 28 lines at 22 distinct places, EVERY compile, exit 0,
    simulation correct. Icarus is saying it will make the process
    sensitive to the whole vector instead of the selected bits: MORE
    sensitivity, not less. Rule: a real Icarus failure starts a line with
    `error:` and stops.
  - Verilator `%Error: Exiting due to 12 warning(s)` (19 with -Wall). Not
    a compile error - a policy. sim.mk passes -Wno-fatal. Census in
    two-simulators-two-jobs.md. But FOUR of the twelve are a real bug -
    link there, do not bury it.
  - cocotb `DeprecationWarning: The 'units' argument has been renamed to
    'unit'.` - your code is 1.x. Harmless today.
  - cocotb WARNING lines for a FAILING test: cocotb logs an assertion
    failure at WARNING level, so yellow is where your real failure is.
    Say this explicitly - students look for red.
  - `make: *** [lab.mk:64: check] Error 1` under a FAIL verdict. Correct
    and expected: the verdict exits non-zero on purpose so it is usable
    from CI. That is the verdict talking, not a broken Makefile.
  - `ValueError: Can't convert LogicArray to int: it contains non-0/1
    values` - this one IS real. It means the design put X on a pin.
  - `Could not initialize GTK!  Is DISPLAY env var/xhost set?` - GTKWave
    with no display.
  - Every entry needs a verbatim string. Do not paraphrase a tool.

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
