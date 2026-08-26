# Directed, random, and the gap between them

**Question this page answers:** *Should I write tests by hand or generate them?*

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
    Should I write tests by hand or generate them?

What this page must contain:
  - Both, and the page is about which bugs each one CANNOT find.
  - Directed: you choose the situation, so you can reach a corner on
    purpose - and you can only reach corners you have thought of.
  - Random: it reaches situations you did not think of, at a rate you can
    afford, and it needs a golden model because nobody can hand-check 600
    instructions.
  - THE MEASURED GAP, and it is the reason this page exists. A 20-program
    x 30-instruction random test compared instruction-by-instruction
    against golden.py - 600 random instructions - MISSES B03 (a flag bug)
    and MISSES B07 (LOAD reading through the wrong register) entirely.
    Verified. Random stimulus with no coverage model does not find a flag
    bug, and it does not find a bug that needs two operands to be
    different.
  - The fix is not more random. It is CONSTRAINED random plus a coverage
    list: bias the generator toward distinct operands, all four shift
    amounts, backward branches, and then measure whether it got there.
    Ties directly back to coverage-is-a-question.md.
  - Reproducibility: cocotb prints its seed on every run
    (`Seeding Python random module with ...`). A random failure you cannot
    replay is not a bug report. Show the real line and how to pin it.
  - Reflex rule.
  - Forward to: the-handshake-is-the-contract.md

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
