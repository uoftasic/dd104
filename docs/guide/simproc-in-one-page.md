# SimProc in one page

**Question this page answers:** *What is this processor, exactly? I need to know what it should do before I can say it does not.*

> **This page has not been written yet.** It is on the DD104 outline and it has an author.
> Until it lands, the material it will cover is in
> [`labs/common`](https://github.com/uoftasic/dd104/tree/main/labs/common) — the package runs
> today with `make` alone.
>
> Something you needed and could not find? Say so in the
> [team Discord](https://discord.gg/hrJnP5UsGz).
 simproc_system
    (UART command FSM) -> simproc (CPU) -> ALU, register_file,
    program_counter; plus dp_ram (2-port, 64x8) and UART_wrapper.
  - The pin map, decoded: ui_in[0]=uart_rx; uo_out[0]=uart_tx,
    uo_out[1]=halt, uo_out[2]=done; uio_in[7:0] sets
    clk_per_bit = {uio_in, 2'b00} (divider = uio_in x 4); rst_n is ACTIVE
    LOW and the wrapper inverts it to an active-high synchronous reset.
  - Four 8-bit registers. R0 IS NOT HARDWIRED TO ZERO - it is an ordinary
    register, and that matters.
  - The ISA summary table. FULL table belongs in
    reference/simproc-instruction-set.md; this page carries the shape:
    8-bit instruction word, two field layouts (register form AA BB oooo,
    branch form dddd oooo), 11 implemented opcodes, 3 unimplemented
    (0xC/0xD/0xE - 3 cycles, PC+1, no state change, no `done` pulse).
  - The FSM: IDLE, CYCLE_1..CYCLE_5, what each cycle does, and the
    MEASURED cycle counts - ORI 5; ADD/SUB/NAND/SHL/SHR/LOAD 4;
    STORE/JMP/BZ/BNZ/BPZ 3. In free-run there is no IDLE between
    instructions; a single STEP costs one extra IDLE cycle.
  - Flags are written ONLY by ADD/SUB/NAND/SHIFT (CYCLE_3) and ORI
    (CYCLE_4). LOAD, STORE and all four branches leave N and Z alone.
    Measured.
  - Branch target = PC_of_instruction + 1 + SE(instr[7:4]), range -8..+7.
    Measured from PC=20: JMP -8 -> 13, JMP +7 -> 28.
  - Memory has NO RESET (dp_ram), which is what lets you load a program,
    reset the core, and run. Registers DO reset to 0.
  - The UART debug protocol: EVERY command is exactly three bytes (cmd,
    addr, data), even when addr/data are ignored. 0xA3 READ, 0x5C WRITE,
    0xF0 PING (replies 0xAA), 0x3F RUN, 0xC7 HALT, 0x6D STEP, 0x99 SET_PC
    (IDLE only), 0xB2 GET_PC.
  - The cost, measured at clk_per_bit=32: one 3-byte command 1,104 cycles;
    PING with reply 1,353; a 64-byte program over the wire 70,656 cycles;
    the same program through the memory backdoor 2. Hence the backdoor.
  - The ORI decision: DD104 specifies ORI as RF[0] <- RF[0] | ZE(instr[7:3])
    and the fork deletes upstream's two `// change this to 1` comments.
    Reasoning: courses/dd104/ORI-DECISION.md. Do NOT reproduce the deleted
    comments on this page - a course whose premise is "there are hidden
    bugs in this file" must not print a planted clue pointing at correct
    code.
  - Forward to: the-golden-model.md

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
