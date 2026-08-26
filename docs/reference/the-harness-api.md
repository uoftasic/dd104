# The SimProc harness

**Question this page answers:** *What can I ask the harness for, and what does it already do for me?*

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
    What can I ask the harness for, and what does it already do for me?

What this page must contain:
  Reference card for labs/common/simproc.py, simproc_asm.py and golden.py.
  The package README is the tutorial; this is the lookup table. Keep them
  consistent or delete one.
  - SimProc(dut) / await sp.start() - clock, reset, RAM blanked to 0x0C.
  - await sp.run(prog) -> exact cycle count; sp.step(n); sp.run_cycles(n).
  - sp.reg(i), sp.regs(), sp.pc(), sp.flags(), sp.fsm(), sp.describe().
  - sp.peek(a), sp.poke(a, v) - the memory backdoor, and WHY it exists
    (measured: 70,656 cycles over the UART vs 2 through the backdoor).
  - sp.halt, sp.done as '0'/'1'/'x'.
  - await sp.count_done_pulses(n), count_halt_cycles(n).
  - await sp.uart_ping(), uart_read(a), uart_write(a, v), set_baud(u).
  - await trace(sp, n, model=g).
  - simproc_asm: ORI/ADD/SUB/NAND/SHIFT/LOAD/STORE/JMP/BZ/BNZ/BPZ, labels,
    and the text-block form.
  - THE TWO THINGS THAT COST AN HOUR IF YOU MEET THEM THE HARD WAY:
      * load() writes a `JMP -1` after your program. There is no way to
        stop this core after exactly N instructions - HALT arrives over
        the UART and takes 1,104 cycles while the core keeps running - so
        programs park themselves and run() watches for the parking
        address.
      * A reset clears the registers and NOT the RAM (dp_ram has no
        reset). That is what lets you load, reset, and run from a known
        state.
  - The make variables: TB=, BUG=, SIM=. TB names a MODULE, not a file.

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
