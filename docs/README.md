# DD104 — Pre-Silicon Verification

Find the bugs hidden in a real 8-bit processor, using cocotb, Icarus Verilog and Verilator,
before they cost a mask set.

Part of the UofT ASIC Team education materials, published at <https://uoftasic.com/dd104/>.
The labs run in the workbench: the IIC-OSIC-TOOLS container you start from the `workspace` clone
you set up in [IC101](https://uoftasic.com/ic101/). You get this course's files with
`mod add dd104`; [Lab 01, Part 1](labs/lab-01-the-adder-you-already-trust-overview.md#part-1-set-up)
walks you through it.

## Who this course is for

You have finished the digital track up to DD103: you can write SystemVerilog, simulate it, and
take it through a flow to layout. Nothing in that flow checked whether the design computes what
you meant. This course is about that gap.

SimProc is an 8-bit processor written by students on this team and wrapped for a real chip
(a TinyTapeout shuttle): an ALU, four registers, 64 bytes of memory and a UART, about 1,200
lines of SystemVerilog. It shipped with one test, and that test passes on a processor whose `SUB`
has its operands swapped and computes `B - A`. DD104
ships thirteen broken versions of SimProc, each a one-line edit, and all thirteen pass that
test. By the end of the course you will have a test suite that catches all thirteen, and a
written bug report for one of them.

| | |
|---|---|
| Track | Digital |
| Prerequisites | [IC101](https://uoftasic.com/ic101/), then [DD101](https://uoftasic.com/dd101/), [DD102](https://uoftasic.com/dd102/) and [DD103](https://uoftasic.com/dd103/), in that order |
| Tools | cocotb 2.0.1, Icarus Verilog 14.0, Verilator 5.050, Surfer and GTKWave, all in the workbench image `hpretl/iic-osic-tools:2026.08` |
| Machine | The workbench you already have. No PDK, no LibreLane, no synthesis. Most runs take under ten seconds; the longest, Lab 06's `make check-all`, takes about four and a half minutes. |
| Total time | 16–20 hours, self-paced |

Check your cocotb version before you search the web for help: `cocotb-config --version` should
print `2.0.1`. Most cocotb tutorials online are for 1.x. Three things they use are errors in 2.x:
`cocotb.fork` (use `cocotb.start_soon`), `@cocotb.coroutine` (use a plain `async def`) and
`dut.sig <= 1` (use `dut.sig.value = 1`). Most of the rest, such as `units=`, `MODULE=` and
`.value.integer`, still runs and only prints a deprecation warning.
[cocotb 2.x and older tutorials](guide/cocotb-2x-vs-every-tutorial.md) has the full list.

## Course path

Work down this table in order. A Read row is guide pages: reading only, no commands. A Do row
is one lab writeup, where every command in the course lives. Each lab's "Before you start"
section repeats which pages it expects you to have read.

| # | | Pages | Time |
|---|---|---|---|
| 1 | Read | [Getting started](guide/getting-started.md) · [What a passing test proves](guide/it-works-is-not-a-result.md) · [What a testbench is](guide/what-a-testbench-is.md) · [Your first cocotb test](guide/your-first-cocotb-test.md) · [The lazy testbench](guide/the-lazy-testbench.md) · [Coverage as a question](guide/coverage-is-a-question.md) | 1 h 15 min |
| 2 | Do | [Lab 01: The adder you already trust](labs/lab-01-the-adder-you-already-trust-overview.md). Set up, watch a reasonable testbench pass on a broken adder, then make it fail. | 1 h 30 min |
| 3 | Read | [Clocks, resets and triggers](guide/clocks-resets-and-triggers.md) · [cocotb 2.x and older tutorials](guide/cocotb-2x-vs-every-tutorial.md) · [Driving and checking a design](guide/driving-and-checking.md) · [Waveforms](guide/waveforms.md) | 1 h |
| 4 | Do | [cocotb on a counter](labs/cocotb-intro-overview.md) (not numbered, but not optional). Triggers, the 1.x traps, a check that passes the good counter and fails a broken one, and waveforms. | 1 h 15 min |
| 5 | Read | [Two simulators](guide/two-simulators-two-jobs.md) · [SimProc in one page](guide/simproc-in-one-page.md) | 45 min |
| 6 | Do | [Lab 02: The only test this chip has](labs/lab-02-the-only-test-this-chip-has-overview.md). Run the shipped test against all thirteen broken cores, then write a better one. | 1 h 45 min |
| 7 | Read | [Flags as architectural state](guide/flags-are-state.md) | 20 min |
| 8 | Do | [Lab 03: Three blocks before the processor](labs/lab-03-three-blocks-before-the-processor-overview.md). Unit-test three SimProc modules, including all 393,216 ALU vectors. | 2 h |
| 9 | Read | [The golden model](guide/the-golden-model.md) · [Where bugs hide](guide/where-bugs-hide.md) · [Directed and random tests](guide/directed-random-and-the-gap.md) | 1 h |
| 10 | Do | [Lab 04: Your first bug hunt](labs/lab-04-your-first-bug-hunt-overview.md). Get a mystery core, find the bug, and prove the fix with a test. | 2 h 30 min |
| 11 | Read | [Handshakes and timing](guide/the-handshake-is-the-contract.md) | 25 min |
| 12 | Do | [Lab 05: Every answer is right](labs/lab-05-every-answer-is-right-overview.md). Two cores where every value is correct and the chip is still broken. | 1 h 15 min |
| 13 | Read | [Writing the bug report](guide/writing-the-bug-report.md) | 25 min |
| 14 | Do | [Lab 06: Capstone](labs/lab-06-capstone-overview.md). One suite that catches all thirteen, and a written bug report. | 3 h 30 min |

Keep these open in a tab while you work. They are for looking things up, not for reading
start to finish:

- [The SimProc instruction set](reference/simproc-instruction-set.md)
- [The SimProc harness](reference/the-harness-api.md)
- [Output that is not an error](reference/output-that-is-not-an-error.md)

## Getting help

Ask in the [team Discord](https://discord.gg/hrJnP5UsGz). Nobody expects you to work this out
alone. [Getting started](guide/getting-started.md#getting-help) says what to include in a
question so it can be answered quickly.

## Next courses

- DD201 — High-Level Synthesis
- DD202 — Computer Architecture
