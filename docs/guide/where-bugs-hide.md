# Where bugs hide

**Question this page answers:** *The bugs I am hunting are one line each. Why can I not just read the file?*

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
    The bugs I am hunting are one line each. Why can I not just read the file?

What this page must contain:
  - THE THESIS: a hidden bug is not a subtle bug. It is a bug whose wrong
    behaviour AGREES with the right behaviour on exactly the inputs a
    person naturally picks. Every one of the thirteen is one line, and you
    could read all thirteen in a minute if you knew which lines to read.
  - The taxonomy, with a SimProc example each. Name the bug ID; NEVER print
    the edit.
      * SYMMETRY. A - B == B - A whenever A == B. 512 of 65,536 pairs
        survive an operand swap, and `SUB rX, rX` (clear a register) is in
        that 512. Same trap in NAND: `NAND rX, rX` is the only way to write
        NOT in this machine, and it is exactly where NAND and NOR agree
        (256 of 65,536 pairs). B01, B02.
      * ALIASING. Two operands that happen to be the same register. `LOAD
        r1, r1` - loading through a pointer into itself - is a real idiom
        and is correct under B07. The author of this course's own first
        draft of that test used it and caught nothing. TELL THAT STORY: a
        testbench author's blind spot found by injecting the bug is worth
        more than the bug.
      * THE DEFAULT VALUE. Shift by 1 is what everybody writes; shift by 2
        and 3 are where B06 lives. The UART's default baud is where B12
        does NOT live - measured: B12 is behaviourally identical to clean
        at clk_per_bit >= 32, PING still answers 0xAA at 16, nothing works
        at <= 8.
      * RESET. After reset every register is 0, so `0 | imm` and `0 + imm`
        agree, and so do "the right register" and "the wrong register".
        The FIRST instance of the instruction is always correct;
        divergence starts at the second. B10, B11.
      * ONE SIDE OF THE NUMBER LINE. Zero-extending a signed displacement
        leaves every FORWARD branch exactly right (+0..+7) and sends every
        backward branch 16 too far. "Skip the next instruction" passes;
        the first loop never terminates. B05.
      * STATE YOU FORGOT WAS STATE. Flags. Handshake pins. Cycle counts.
        Forward to flags-are-state.md and
        the-handshake-is-the-contract.md.
  - The measured punchline for the random-stimulus reader: T08's 600
    random instructions miss B03 entirely, and miss B07 entirely. Random
    without a coverage model is not a safety net.
  - Reflex rule: make every operand distinct on purpose; sweep every field;
    run each instruction TWICE.
  - Forward to: directed-random-and-the-gap.md

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
