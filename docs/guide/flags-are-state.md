# Flags are architectural state

**Question this page answers:** *I checked the answer and it was right. What else is there to check?*

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
    I checked the answer and it was right. What else is there to check?

What this page must contain:
  - N and Z are not debug output. They are architectural state: the only
    way this machine makes a decision, and they persist between
    instructions.
  - Measured facts to build on: N = ALUout[7], Z = ~(|ALUout), pure
    combinational functions of the result. Flags are written ONLY by
    ADD/SUB/NAND/SHIFT (CYCLE_3) and ORI (CYCLE_4); LOAD, STORE and all
    four branches leave them alone.
  - Demonstrate the value/flag split with real numbers from B03: value
    mismatches 0 EVERYWHERE, flag mismatches ADD 3840, SUB 3840, OR 255,
    NAND 255, SHL 14400, SHR 3136. Every one of those is derivable by
    hand and the derivation is the lesson - ADD/SUB is 15 nonzero results
    with a zero low nibble x 256 pairs = 3840; OR is A[3:0]=B[3:0]=0 (256
    pairs) minus the genuinely-zero case = 255. Have the student close one
    of them by hand.
  - Then the second half: a flag is only useful if it SURVIVES until the
    branch that reads it. Two branches off one compare (`BZ ...; BNZ ...`)
    is a day-one idiom and it is where B09 lives. One branch after a
    compare works perfectly.
  - The prior being overwritten: "the compare is still valid" is an
    assumption, and it is testable.
  - Reflex rule: after every operation, assert the value AND both flags;
    and test that a flag survives an instruction that should not touch it.
  - Forward to: where-bugs-hide.md

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
