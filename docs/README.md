# DD104 — Pre-Silicon Verification

An 8-bit processor with bugs hidden in it, and the tools to find them before they cost a mask
set.

Part of the **UofT ASIC Team** education materials. Published at **https://uoftasic.com/dd104/**.
Labs run inside the shared **workspace** you set up in [IC101](https://uoftasic.com/ic101/).

## At a glance

| | |
|---|---|
| **Track** | Digital |
| **Prerequisites** | [IC101](https://uoftasic.com/ic101/) → [DD101](https://uoftasic.com/dd101/) → [DD102](https://uoftasic.com/dd102/) → [DD103](https://uoftasic.com/dd103/), in that order |
| **Tools** | cocotb, Icarus Verilog, Verilator, Surfer / GTKWave — all inside the workbench |
| **Time** | 16–20 hours, self-paced |
| **Machine** | The same workbench you already have. **No PDK, no LibreLane, no synthesis.** The longest thing you run is about a minute; most of it is under ten seconds. |

> **This course is pinned to the workbench image `hpretl/iic-osic-tools:2026.04`**, which
> ships **cocotb 2.0.1**, **Icarus Verilog 14.0** and **Verilator 5.046**.
>
> Check yours: `cocotb-config --version` should say `2.0.1`.

> ### ⚠ Most cocotb tutorials you will find are 1.x. Three things break; the rest only warn.
>
> Almost everything a search engine returns is cocotb 1.x, and cocotb 2.0 changed some of it.
> **Three changes are hard errors:** `cocotb.start_soon`, not `cocotb.fork`; `async def`, not
> `@cocotb.coroutine`; `dut.sig.value = 1`, not `dut.sig <= 1`.
>
> Everything else you have read about — `units=`, `MODULE=`, `.value.integer` — **still runs on
> the cocotb in your container** and only prints a deprecation warning. Write the new spellings
> anyway; a deprecation is a countdown. But do not go looking for a failure that is not there.
> Full breakdown, measured: [cocotb 2.x vs every tutorial](guide/cocotb-2x-vs-every-tutorial.md).

> **Every lab runs with `make` alone**, from a clone of this repo, with no environment setup —
> and every one of them prints a verdict rather than a shrug. If a setup step fails at 2 a.m.,
> type `make` anyway.

## The argument

SimProc is a real 8-bit processor: an ALU, four registers, 64 bytes of memory, a UART you can
talk to, about 1,200 lines of SystemVerilog written by students on this team and wrapped for a
real chip.

It shipped with one test. That test sets an input pin high, waits a hundred clock cycles, and
asserts the output byte equals 3 — which, decoded against the pin map, means *the processor is
not running*.

DD104 ships **thirteen deliberately broken versions of that processor**, each one a single-line
edit. All thirteen pass the shipped test.

**The only test this chip has, passes on a processor whose `SUB` is backwards.** Everything in
this course follows from that sentence.

## What you'll do

1. Watch a perfectly reasonable testbench pass on a **broken** 4-bit adder, then make it fail
2. Point a real coverage tool at your own stimulus and have it find the input you forgot
3. Walk **393,216** ALU vectors and find three bugs by brute force
4. Be dealt a **mystery core** and hunt a bug nobody has named for you
5. Debug two processors on which **every register, flag and byte of memory is correct**
6. Finish with a test suite that catches all thirteen — and a written bug report for one

## Path

| Part | Guide | Lab |
|------|-------|-----|
| 0 | [Getting started](guide/getting-started.md) | — |
| I — Why "it works" is not a result | **["It works" is not a result](guide/it-works-is-not-a-result.md)** · [What a testbench actually is](guide/what-a-testbench-is.md) · [The lazy testbench](guide/the-lazy-testbench.md) · [Coverage as a question](guide/coverage-is-a-question.md) | [Lab 01](labs/lab-01-the-adder-you-already-trust-overview.md) |
| II — The tools that do the doubting | [Your first cocotb test](guide/your-first-cocotb-test.md) · [Clocks, resets and triggers](guide/clocks-resets-and-triggers.md) · **[cocotb 2.x vs every tutorial](guide/cocotb-2x-vs-every-tutorial.md)** · [Driving and checking](guide/driving-and-checking.md) · [Waveforms](guide/waveforms.md) · [Two simulators, two jobs](guide/two-simulators-two-jobs.md) | [Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md) |
| III — The machine under test | [SimProc in one page](guide/simproc-in-one-page.md) · [The golden model](guide/the-golden-model.md) · [Flags are architectural state](guide/flags-are-state.md) | [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) |
| IV — How bugs hide | [Where bugs hide](guide/where-bugs-hide.md) · [Directed, random, and the gap](guide/directed-random-and-the-gap.md) | [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md) |
| V — Right answers, broken chip | [The handshake is part of the contract](guide/the-handshake-is-the-contract.md) | [Lab 05](labs/lab-05-every-answer-is-right-overview.md) |
| Capstone | [Writing the bug report](guide/writing-the-bug-report.md) | [Lab 06](labs/lab-06-capstone-overview.md) |

> **Every page above is written, and all six lab packages run today with `make` alone.** Each
> lab writeup carries the theory it needs; the harness is documented page by page in
> [The SimProc harness](reference/the-harness-api.md) and in
> [`labs/common/README.md`](https://github.com/uoftasic/dd104/blob/main/labs/common/README.md).
> If something leaves you stuck, say so in Discord.

**Stuck?** Ask in the [team Discord](https://discord.gg/hrJnP5UsGz). Nobody expects you to work
this out alone at 2 a.m. — see [Getting help](guide/getting-started.md#getting-help).

Reference: [The SimProc instruction set](reference/simproc-instruction-set.md) ·
[The SimProc harness](reference/the-harness-api.md) ·
[Output that is not an error](reference/output-that-is-not-an-error.md)

## Quick start

```bash
# in the noVNC desktop, after IC101
. /foss/designs/common/.designinit
mod add dd104          # first time only
mod dd104
cocotb-config --version                            # expect: 2.0.1
cd labs/lab-01-the-adder-you-already-trust && make # ends on VERDICT: FAIL, on purpose
```

## What you'll have at the end

A testbench that catches all thirteen bugs in a real processor, and — more useful than the
testbench — the habit of asking, of any green test anywhere, *what would this have caught?*

## Next courses

- **DD201** — High-Level Synthesis
- **DD202** — Computer Architecture
