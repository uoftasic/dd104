# Writing the bug report

**Question this page answers:** *I found it. What do I actually hand to the designer?*

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
    I found it. What do I actually hand to the designer?

What this page must contain:
  - The deliverable of verification is not a red test. It is a report
    someone can act on without re-deriving your week.
  - The five parts, each with a worked SimProc example:
      1. The smallest program that reproduces it. Minimise: cut
         instructions until it stops failing, then put the last one back.
      2. Expected vs actual, as numbers, with the arithmetic shown.
      3. The shape - how many vectors, and what the count implies.
      4. Where it is NOT: what still works. This is what makes a report
         credible and it is what localises the fix.
      5. The one-line reflex the test suite gained, so it never comes back.
  - Worked example end to end on one Tier-1 bug the student has already
    found by the time they read this page. Do NOT introduce a new one.
  - Regression: the report is finished when there is a test in the suite
    that fails before the fix and passes after. `make check BUG=...` is
    that, mechanised.
  - Close the course: point back at test/test.py from
    it-works-is-not-a-result.md and ask the student to write the one-line
    claim their own suite now supports. It should be an uncomfortably
    long sentence, and that is the whole point.
  - Forward to: labs/lab-06-capstone.md, then DD201 and DD202.

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
