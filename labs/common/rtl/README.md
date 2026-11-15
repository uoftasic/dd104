# `labs/common/rtl`: the SimProc under test

This is the processor every SimProc lab runs against. It is a fork of the RTL that was submitted to
a TinyTapeout shuttle, rather than a mock-up written for teaching.

## Provenance

```
repo    git@github.com:uoftasic/simproc.git   (branch main)
commit  1d97772cd933faeb5d330074d0dc58b07378f15c
        "Merge pull request #1 from ieeeuoft-asic/vprajapati/mem-64"
        Vraj Prajapati, Mon Nov 10 12:06:29 2025 -0600
blob    src/simproc_system.sv   3c19a1b45c9b4e51f05f8ef73859ee13a4a3c329   (1178 lines)
sha256  5da82589f8b045a92f0390093118394f029df9723711aa957ecd2fcadfcf3dbe
```

## What DD104 changed

DD104 changed four lines, and all four are comments. There are no logic changes and the line count is identical,
so every line number in `bugs.py` and in every lab writeup is also an upstream line number.

| line | upstream | here |
|---|---|---|
| 634 | `// rA <- RF[0]` | `// ORI's accumulator is R0 (DD104 spec; see ORI-DECISION.md)` |
| 635 | `rf_reg_a_in = 2'b0; // change this to 1, to match SimProc` | `rf_reg_a_in = 2'b0;` |
| 688 | `// RF[0] <- ALU out (change later to be SimProc accurate)` | `// RF[0] <- ALU out.  ORI's accumulator is R0 (DD104 spec).` |
| 689 | `rf_reg_w_in = 2'b0; // change this to 1, to match SimProc` | `rf_reg_w_in = 2'b0;` |

You can confirm this yourself:

```bash
diff <(sed 's/[[:space:]]*$//' /path/to/simproc/src/simproc_system.sv) \
     <(sed 's/[[:space:]]*$//' rtl/simproc_system.sv)
```

We changed them because DD104's premise is that there are hidden bugs in this file. A comment reading *"change
this to 1"* next to code that is not wrong reads as a planted clue, and it points at correct
code. The full argument, including the four simulated variants that show `R0` and `R1` are
exactly isomorphic, is in [`ORI-DECISION.md`](../../../ORI-DECISION.md).

`tt_um_ieeeuoftasic_simproc.sv` is byte-identical to upstream
(`sha256 cb8f2269c6888f58d50020c5805dc99e33f6b3a7b34cd9ec0a94023b02d49551`).

`tb.v` is DD104's, and is the only file here that is not from the SimProc repo. It is the
TinyTapeout testbench shell with the waveform dump made conditional on `+WAVES`.

## What is in the file

| lines | module | what it is |
|---|---|---|
| 1–117 | `simproc_system` (ports) | the top of the system |
| 118–320 | `simproc_system` (UART FSM) | the 3-byte debug command protocol |
| 321–739 | `simproc` | the CPU: a 6-state FSM, `IDLE` and `CYCLE_1`..`CYCLE_5` |
| 741–771 | `register_file` | four 8-bit registers, two combinational read ports |
| 773–788 | `program_counter` | |
| 789–823 | `ALU` | six operations, `N` and `Z`, no carry and no overflow |
| 826–858 | `dp_ram` | 64 bytes, two ports, combinational reads, no reset |
| 860–1178 | `UART_wrapper`, `UART_TX`, `UART_RX` | 8N1, no parity |

Instance path from the testbench:

```
tb
└── tt_um_ieeeuoftasic_simproc          the pin frame
    └── U1                              simproc_system
        ├── RAM1.mem[0..63]             the memory
        ├── UART1                       the serial link
        └── CPU1                        the core
            ├── curr_state              IDLE / CYCLE_1..CYCLE_5
            ├── n_flag_out, z_flag_out
            ├── RF1.rf[0..3]            the registers
            ├── PC1.pc_out
            └── ALU1
```

`simproc.py` wraps all of those; you should not need to type these paths yourself.

## Output that looks like failure

Compiling this design with `iverilog -g2012` prints 28 `sorry:` notes of the form

```
rtl/simproc_system.sv:552: sorry: constant selects in always_* processes are not fully
supported (the process will be sensitive to all bits in 'instr_reg_out[7:0]').
```

at 22 distinct locations: 543, 544, 552 ×2, 553, 555, 571, 573, 579, 587, 595, 610 ×2,
611 ×2, 613, 621 ×2, 633, 644 ×2, 645 ×2, 648, 660, 662, 674, 677. These are notes rather
than errors. Icarus is saying that it will make the process sensitive to the whole vector instead
of only the selected bits, which means more sensitivity than the code asks for, never less. The
exit code is 0 and the simulation is correct. A real Icarus failure starts a line with `error:` and
stops.

Verilator refuses to build the design at all. `verilator --lint-only` on this design prints 12
warnings and then:

```
%Error: Exiting due to 12 warning(s)
```

The twelve are six `WIDTHTRUNC`, four `WIDTHEXPAND` and two `CASEINCOMPLETE` (`-Wall` raises the
count to 19), which is why `sim.mk` passes `-Wno-fatal` when `SIM=verilator`. Four of the twelve are the same finding
at four different lines, and it is a real one:

```
%Warning-WIDTHTRUNC: rtl/simproc_system.sv:848:16: Bit extraction of array[63:0] requires
                     6 bit index, not 8 bits.
                   : ... note: In instance 'tt_um_ieeeuoftasic_simproc.U1.RAM1'
  848 |             mem[addr_a] <= din_a;
```

(The same warning appears at lines 851, 856 and 857, the RAM's other three port accesses.)

The RAM has 64 entries, but the address bus is 8 bits wide. Verilator finds that mismatch just by
reading the file. Icarus finds it only at run time, as eight X bits on the chip's TX pin, and only
if you ever read an address above 63. Neither tool is wrong, but Verilator tells you in 0.4 seconds.
