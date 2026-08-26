# SimProc in one page

**Question this page answers:** *What is this processor, exactly? I need to know what it should
do before I can say it does not.*

`rtl/simproc_system.sv` is 1,178 lines. You are not going to read it, and you do not need to.
The **machine** is small enough to hold in your head, and everything you will be asked to do in
DD104 is a question about the machine rather than about the file.

Here is the whole of it.

## All the state there is

```
    r0  r1  r2  r3        four 8-bit registers                 32 bits
    PC                    one 8-bit program counter             8 bits
    N   Z                 two flags                             2 bits
    mem[0 .. 63]          sixty-four bytes of RAM             512 bits
                                                              ────────
                                                              554 bits
```

That is the entire architectural state of this processor. If two SimProcs agree on those 554
bits after every instruction, they are the same machine as far as any program can tell — which
is exactly the claim [the golden model](guide/the-golden-model.md) is built to check, and exactly
the claim [Lab 05](labs/lab-05-every-answer-is-right-overview.md) shows is not enough.

> **The prior this page overwrites.** If you have met RISC-V or MIPS, you know that register
> zero reads as zero and swallows writes. **`r0` here is an ordinary register.** It holds
> whatever you last put in it, and `ORI` — the only instruction that can introduce a constant —
> writes `r0` and nothing else. Assuming otherwise will cost you an evening, and
> [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) asks you to prove it to
> yourself in two lines of test.

Three absences shape every program you will write:

- **No carry flag and no overflow flag.** Eight-bit arithmetic wraps and nothing tells you.
  `200 + 60` is `4`.
- **No compare instruction.** `SUB` is the compare, which means comparing *destroys* one of the
  values.
- **No `NOT`, no `HALT`, no stack, no call, no interrupt.** `NAND rX, rX` is how you invert.
  A program that is finished parks itself in `JMP -1`.

## One byte, one instruction

Every instruction is exactly one byte, and three field layouts share the encoding space:

```
    register form     A A B B o o o o      rA = instr[7:6], rB = instr[5:4]
    branch form       d d d d o o o o      d = 4-bit SIGNED displacement
    3-LSB forms       A A D S S 0 1 1      SHIFT: D = direction, SS = amount
                      i i i i i 1 1 1      ORI:   5-bit immediate
```

`rA` is **both a source and the destination** in the register form: `ADD(1, 2)` means
`r1 = r1 + r2`. There is no three-operand instruction on this machine.

Eleven instructions exist. The complete encoding table, with what each one does and what it
costs, is [The SimProc instruction set](reference/simproc-instruction-set.md) — keep that one
open in another tab. The short version:

| | |
|---|---|
| arithmetic and logic | `ADD` `SUB` `NAND` `SHL` `SHR` — all write `rA`, all set `N` and `Z` |
| the constant | `ORI imm5` — `r0 <- r0 \| imm`, sets flags |
| memory | `LOAD rA, rB` reads `mem[rB]`; `STORE rA, rB` writes `mem[rB]` |
| control | `JMP` always; `BZ` `BNZ` `BPZ` on the flags — **none of them touch the flags** |
| nothing | `0xC` `0xD` `0xE` are unimplemented and behave like a very slow no-op |

## The FSM is the timing

The core is a six-state machine: `IDLE`, then `CYCLE_1` … `CYCLE_5`. It is not pipelined,
there is no cache, and nothing is speculative — so the cycle count of a program is the sum of
the cycle counts of its instructions, and you can add it up by hand before you run it.

```
    IDLE ──run──> CYCLE_1 ──> CYCLE_2 ──> CYCLE_3 ──┬──> back to CYCLE_1        3 cycles
                  fetch        read rA,rB   decode  │    STORE and all branches
                  PC <- PC+1                        │
                                                    ├──> CYCLE_4 ──> CYCLE_1    4 cycles
                                                    │    write back  ADD SUB NAND SHL SHR LOAD
                                                    │
                                                    ├──> CYCLE_4 ──> CYCLE_5    5 cycles
                                                    │    ORI: OR, then write r0
                                                    │
                                                    └──> IDLE ──> CYCLE_1       4 cycles
                                                         0xC 0xD 0xE
```

Read that diagram twice, because two of its edges are load-bearing.

**`CYCLE_2` reads the register file for every instruction**, using `instr[7:6]` and
`instr[5:4]` as the two register numbers — before anything has decided what the instruction
*is*. On a branch those bits are half of the displacement, and the read happens anyway and is
thrown away. That is why a bug in the register-select path can show up on instructions that do
not obviously use registers.

**An unimplemented opcode leaves through `IDLE`.** It matches no clause in `CYCLE_3`, so the
FSM takes its default exit, spends one cycle in `IDLE`, and is sent back to `CYCLE_1` by the
still-asserted `run`. Three consequences, all measured:

| four filler bytes (`0x0C`) | |
|---|---|
| clock cycles | **16** — four each, not three |
| `done` pulses | **0** |
| cycles with `halt` high | **4** — one per instruction |

So the byte the harness fills unwritten memory with is also the one byte in the instruction set
that makes `halt` blink in the middle of a running program. If you write the assertion
*"`halt` must stay low while `run` is asserted"* — and [Lab 05](labs/lab-05-every-answer-is-right-overview.md)
asks you to — it will fire on any program that walks off its own end into filler. That is your
test working correctly on a machine that is behaving as designed, which is a distinction worth
meeting here rather than at midnight.

### Cycle counts, and a sum you can check

| instruction | cycles |
|---|---|
| `ORI` | 5 |
| `ADD` `SUB` `NAND` `SHL` `SHR` `LOAD` | 4 |
| `STORE` `JMP` `BZ` `BNZ` `BPZ` | 3 |
| `0xC` `0xD` `0xE` (unimplemented) | 4, no `done`, one cycle of `halt` |

The model can run a program with no simulator underneath it at all:

```bash
cd labs/common
make model
```

```
16 instructions in memory, 28 executed, 109 clock cycles
registers: r0=32 r1=15 r2=1 r3=32
mem[0x20] = 15   (all 28 instructions executed)
```

**109 is GOLDEN**, and it is a number you can derive rather than trust: seven instructions of
setup at `4+5+4+4+4+5+4 = 30`, a three-instruction loop body at `4+4+3 = 11` run five times for
`55`, then `4+5+4+4+4+3 = 24` to finish. $30 + 55 + 24 = 109$. The real silicon model agrees
to the cycle — `test_example.t05_a_loop_and_its_cycle_count` asserts exactly this — and if your
hardware ever says 114 instead, five extra cycles over five iterations is one extra cycle per
iteration, which is a much better place to start than "it is slow".

## The memory, and its one sharp edge

`dp_ram` is **64 bytes**, dual-ported, with **combinational reads** and **no reset**.

The no-reset part is a feature you will use constantly: resetting the core clears the
registers, the PC and the flags, and leaves your program and its results exactly where they
were. That is what lets a test load a program, reset, and run from a known state.

The 64-byte part is the sharp edge. The address bus is **8 bits wide** and the array has 64
entries:

- **Reads above 63 return `X`.** A UART `READ` of address `0x45` puts eight undefined bits on
  the chip's TX pin. In cocotb 2.x, `int()` on that raises rather than guessing — which is the
  right behaviour and will look like a harness bug the first time you see it.
- **Writes above 63 are silently dropped**, and they do **not** wrap into low memory. Measured:
  writing `0x99` to `0x45` leaves `mem[0x05]` untouched.
- Verilator finds this by reading the file in 0.4 seconds
  (`Bit extraction of array[63:0] requires 6 bit index, not 8 bits`, four times). Icarus finds
  it at run time, as `X` on a pin. Both are right; only one of them told you before you ran
  anything. That is [Two simulators, two jobs](guide/two-simulators-two-jobs.md).

The harness refuses out-of-range addresses on your behalf with a message that says all of the
above, so you will normally meet this through a *program* whose pointer register went somewhere
you did not intend.

## The chip, from outside

SimProc is wrapped in a TinyTapeout pin frame. From outside the package it has one serial input
pin, one serial output pin, two status pins and a baud divider — and that is the whole
interface.

| pin | direction | what it is |
|---|---|---|
| `ui_in[0]` | in | `uart_rx` — everything goes in here |
| `uo_out[0]` | out | `uart_tx` — everything comes out here |
| `uo_out[1]` | out | `halt` — high while the core sits in `IDLE` |
| `uo_out[2]` | out | `done` — one-cycle pulse as an instruction retires |
| `uo_out[7:3]` | out | tied to zero |
| `uio_in[7:0]` | in | the baud divider: `clk_per_bit = uio_in × 4` |
| `uio_out`, `uio_oe` | out | tied to zero — every bidirectional pin is an input |
| `rst_n` | in | reset, **active low** |
| `ena` | in | always 1 when powered; ignore it |

`uo_out` is where the chip's only test comes from, and decoding it by hand is worth doing once.
`uo_out == 3` is `0b0000_0011`: `uart_tx = 1` (a serial line at rest sits high), `halt = 1`
(the core is in `IDLE`), `done = 0`. **That value asserts that the processor is not running** —
which is the whole reason this course exists, and
[Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md) is where you watch all thirteen
broken cores pass it.

### The debug protocol

The only way in from outside is a **3-byte UART command** — always three bytes, `cmd addr
data`, even when `addr` and `data` are ignored. 8N1, no parity.

| byte | command | what it does |
|---|---|---|
| `0xA3` | `READ` | replies with `mem[addr]` |
| `0x5C` | `WRITE` | `mem[addr] = data` |
| `0xF0` | `PING` | replies `0xAA` |
| `0x3F` | `RUN` | start free-running |
| `0xC7` | `HALT` | stop |
| `0x6D` | `STEP` | execute exactly one instruction |
| `0x99` | `SET_PC` | `PC = addr`, and **only while the core is in `IDLE`** |
| `0xB2` | `GET_PC` | replies with the PC |

Serial is slow, and on this machine "slow" has a number on it. All measured at the default
`clk_per_bit = 32`:

| | clock cycles |
|---|---|
| one 3-byte command | **1,104** |
| a command with a reply (`PING`) | **1,353** |
| loading a 64-byte program over the wire | **70,656** |
| the same program through the harness's memory backdoor | **2** |
| the head start `RUN` gets — the core is already executing this long before the command finishes going out | **57** |

Those numbers are why the harness has a backdoor into the RAM array at all, and why anything in
`simproc.py` that counts something starts its monitor *before* sending `RUN`. They are also why
there is no way to stop this processor after exactly N instructions: `HALT` takes 1,104 cycles
to arrive and the core runs the whole time. Programs park themselves instead, in a `JMP -1`,
the way real bare-metal test code does.

## Where the pieces live

If you do open the file, this is the shape of it, and these are the paths the harness reaches
through:

```
tb
└── tt_um_ieeeuoftasic_simproc          the pin frame
    └── U1                              simproc_system      lines 1–320
        ├── RAM1.mem[0..63]             64 bytes            lines 826–858
        ├── UART1                       8N1, no parity      lines 860–1178
        └── CPU1                        the core            lines 321–739
            ├── curr_state              IDLE / CYCLE_1..CYCLE_5
            ├── n_flag_out, z_flag_out
            ├── RF1.rf[0..3]            the registers       lines 741–771
            ├── PC1.pc_out                                  lines 773–788
            └── ALU1                    6 ops, N and Z      lines 789–823
```

Three of those modules are 16, 31 and 34 lines, which is why
[Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) can finish them completely —
393,216 vectors through the ALU — before anybody asks you to reason about a processor.

`simproc.py` wraps every one of these paths, so you should not need to type them yourself.

## The five facts that will actually cost you

Everything above is background. These five are the ones that turn into a wrong answer at 1 a.m.:

1. **`ORI` only sets bits.** `SUB rX, rX` first, or you get the OR of everything that register
   has ever held. This is the single most common way to write a SimProc program that is wrong
   and looks right.
2. **`ORI` always writes `r0`**, whatever else the program is doing. It has no register field —
   all five spare bits are the immediate.
3. **Branch displacements are measured from the *next* instruction**, because the PC has
   already been incremented by the time the branch computes its target. `JMP(0)` falls through;
   `JMP(-1)` is an infinite loop on itself. Range: `-8` to `+7`, and nothing else.
4. **Flags come from `ADD`, `SUB`, `NAND`, `SHIFT` and `ORI` only.** `LOAD`, `STORE` and every
   branch leave `N` and `Z` exactly as they were — which is a feature, because it lets you
   compare once and branch on it twice. It is also an assumption, and
   [assumptions get tested](guide/where-bugs-hide.md).
5. **Shift amounts are two bits.** 0, 1, 2, 3 — you cannot shift by 4 in one instruction, and
   the assembler refuses rather than silently truncating.

Everything on that list is a place where a wrong implementation and a right one agree on the
inputs you would naturally pick. That is not a coincidence, and it is the subject of
[Where bugs hide](guide/where-bugs-hide.md).

Next: [The golden model](guide/the-golden-model.md), which is this page rewritten as 120 lines
of Python that you can compare the real thing against — and
[The SimProc instruction set](reference/simproc-instruction-set.md), which is the table to keep
open while you work.
