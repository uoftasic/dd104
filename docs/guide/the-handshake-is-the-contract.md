# The handshake is part of the contract

**Question this page answers:** *Every register, every flag and every byte of memory is correct. How can it still be broken?*

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
    Every register, every flag and every byte of memory is correct. How can it still be broken?

What this page must contain:
  - Two of the thirteen bugs leave EVERY architectural result correct.
    B08 and B13. Registers, memory, flags, PC - all right, all the time.
    This page is why that is still a bug.
  - `done` is a one-cycle pulse per retired instruction; `halt` is high in
    IDLE. Together they are the interface between this core and anything
    that drives it. Measured: 9 instructions retired, 8 `done` pulses,
    under B08.
  - THE SHARP EDGE, and it is the best sentence on the page: if your
    scoreboard triggers on `done`, a dropped `done` does not make your
    test FAIL. It makes your test silently stop scoring. A test that stops
    checking and stays green is worse than a test that goes red.
  - B13: functionally identical output, one wasted cycle and a one-cycle
    `halt` blip per STORE. On a real chip that is a performance bug and a
    debugger-visible glitch. Only a protocol assertion sees it.
  - The harness gives you the tools: `count_done_pulses(n)`,
    `count_halt_cycles(n)`, and exact cycle counts from `sp.run()`.
  - The prior being overwritten: "functional equivalence is correctness."
    It is not. Timing and handshake are part of what you shipped.
  - Reflex rule: assert one `done` per retired instruction, and assert
    `halt` stays low for the whole time `run` is asserted.
  - Forward to: writing-the-bug-report.md

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
