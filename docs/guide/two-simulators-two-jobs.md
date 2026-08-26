# Two simulators, two jobs

**Question this page answers:** *Why does this course ship two simulators, and which one should I be running?*

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
    Why does this course ship two simulators, and which one should I be running?

What this page must contain:
  - Icarus is the default because of the number that matters when you are
    debugging: MEASURED, labs/common, six example tests - Icarus 7.8 s,
    Verilator 22.6 s cold (Verilator simulates faster and builds for ~15 s).
    Re-measure both before publishing.
  - Name the scary output before it appears. Icarus prints 28 `sorry:
    constant selects in always_* processes are not fully supported` notes at
    22 distinct places, every compile, exit 0, simulation correct. A real
    Icarus failure starts a line with `error:`.
  - Verilator REFUSES TO BUILD the shipped RTL: `%Error: Exiting due to 12
    warning(s)` at default, 19 with -Wall. Census: 6 WIDTHTRUNC, 4
    WIDTHEXPAND, 2 CASEINCOMPLETE; -Wall adds 4 UNUSEDSIGNAL, 1
    UNUSEDPARAM, 1 PINCONNECTEMPTY, 1 DECLFILENAME. sim.mk passes
    -Wno-fatal for exactly this reason - say so.
  - THE SET PIECE, and it is the page's whole reason to exist. Four of the
    twelve are one real finding at simproc_system.sv lines 848/851/856/857:
        %Warning-WIDTHTRUNC: Bit extraction of array[63:0] requires
                             6 bit index, not 8 bits.
    The RAM is 64 deep; the address bus is 8 bits. Verilator finds it
    STATICALLY in 0.4 s. Icarus finds it at run time, as eight X bits
    arriving on the TX pin, and only if you happen to read a high address.
    Demonstrate both halves: lint, then a UART READ of 0x45 (measured: the
    read returns X; the matching WRITE is silently dropped and does NOT
    alias into low memory - mem[0x05] is still 0x42 afterwards).
  - The prior being overwritten: "a warning is a suggestion." Here one of
    them is a real bug in the address decode of a real chip.
  - Reflex rule: lint before you simulate; an X on a pin is a question, not
    a glitch.
  - Forward to: simproc-in-one-page.md

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
