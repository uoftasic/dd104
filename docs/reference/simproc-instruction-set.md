# The SimProc instruction set

**Question this page answers:** *What does every opcode do, how is it encoded, and how many cycles does it take?*

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
    What does every opcode do, how is it encoded, and how many cycles does it take?

What this page must contain:
  A card, not an essay. Everything here is measured, and the empirical
  classification of all 256 instruction bytes is the proof there are no
  encoding collisions.
  - Encoding layouts: register form `AA BB oooo` (rA=instr[7:6],
    rB=instr[5:4], opcode instr[3:0]); branch form `dddd oooo`; and the two
    3-LSB forms, SHIFT `AA D SS 011` and ORI `iiiii 111`, where the opcode
    is only instr[2:0] and the field grows upward.
  - The full table: opcode, mnemonic, operation, cycles, flags written.
      0000 LOAD  rA <- mem[rB]                              4   no flags
      0001 JUMP  PC <- PC+1+SE(instr[7:4])                  3   no flags
      0010 STORE mem[rB] <- rA                              3   no flags
      0011 SHIFT rA <- rA << instr[4:3] if instr[5] else >> 4   flags
      0100 ADD   rA <- rA + rB                              4   flags
      0101 BPZ   if !N: PC <- PC+1+SE(instr[7:4])           3   no flags
      0110 SUB   rA <- rA - rB                              4   flags
      0111 ORI   R0 <- R0 | ZE(instr[7:3])                  5   flags
      1000 NAND  rA <- ~(rA & rB)                           4   flags
      1001 BNZ   if !Z: PC <- PC+1+SE(instr[7:4])           3   no flags
      1010 BZ    if  Z: PC <- PC+1+SE(instr[7:4])           3   no flags
      1011 = SHIFT (3-LSB alias)                            4   flags
      1100/1101/1110 unimplemented: 3 cycles, PC+1, no state
                     change, and NO `done` pulse
      1111 = ORI (3-LSB alias)                              5   flags
  - The 256-byte classification, which is the no-collision proof: 48
    unimplemented (C,D,E), 64 branch (1,5,9,A), 16 STORE (2), 80 four-cycle
    (0,3,4,6,B), 16 NAND (8), 32 ORI (7,F). 48+64+16+80+16+32 = 256.
  - The ALU: ADD 000, SUB 001, OR 010, NAND 011, SHL 100, SHR 101; ops 6
    and 7 return 8'h00 (so N=0, Z=1 - a DEFINED answer for an undefined
    opcode). SHL/SHR shift by B[1:0]. N = result[7], Z = ~(|result). No
    carry-out, no overflow, 8-bit wrap.
  - Branch range -8..+7, target = PC_of_instruction + 1 + SE(disp).
  - The UART command table (all three bytes, always): 0xA3 READ, 0x5C
    WRITE, 0xF0 PING->0xAA, 0x3F RUN, 0xC7 HALT, 0x6D STEP, 0x99 SET_PC
    (IDLE only), 0xB2 GET_PC.
  - Memory: 64 bytes, 8-bit address bus. Addresses >= 64 read as X and
    writes to them are silently DROPPED - they do not alias into low
    memory (measured: after writing 0x99 to 0x45, mem[0x05] is still
    0x42). Cross-link two-simulators-two-jobs.md, where Verilator finds
    this statically.

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
