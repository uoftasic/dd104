# "It works" is not a result

**Question this page answers:** *I ran my design and it did the thing. Why isn't that
enough?*

By the end of DD103 you had a `.gds` file: a real chip layout, DRC clean, LVS clean, hardened
by a flow that ran eighty stages and printed a green tick at the end of every one of them.
Nobody, at any point in that entire pipeline, looked at whether your design was **right**.

That is not a criticism of the tools. It is a division of labour, and it is worth seeing
clearly, because the gap it leaves is the entire subject of this course.

| The tool | The question it answers | The question it does not answer |
|---|---|---|
| Yosys | can this be built out of gates? | are they the right gates? |
| Verilator lint | is this legal SystemVerilog? | does it compute what you meant? |
| OpenSTA | will the signals arrive in time? | are they the right signals? |
| LibreLane / DRC / LVS | can this be manufactured, and does the layout match the netlist? | does the netlist do anything useful? |

Every one of those can pass, in full, on a processor whose `SUB` instruction computes
`B - A`. It will be a beautiful chip. It will subtract backwards forever.

## The word "works" is hiding three different claims

When you say a design works, you are usually saying one of these and hoping it implies the
others:

1. **It compiled.** The tool accepted it.
2. **It ran.** It did not hang, crash, or emit `x`.
3. **It produced the answer I expected — on the inputs I thought of.**

Only the third is about correctness, and it carries a clause most people do not say out loud:
*on the inputs I thought of.* The inputs you thought of are a sample drawn by the same brain
that wrote the bug. That is the structural problem, and it does not go away by being careful.

> **The prior you are bringing, and where it betrays you.**
>
> **If you came from software:** tests are the chore after the interesting part, and if you
> skip them, you find out in staging and push a fix. The fix is the part that does not
> transfer. There is no `git push` to a chip that has already been manufactured.
>
> **If you came from circuits:** broken things look broken. A floating node reads as an X, a
> shorted output smokes. But an RTL bug is not damage — it is a *different, perfectly
> well-formed circuit* that computes the wrong function, cleanly, at full speed, with clean
> edges on every signal. There is nothing to see. This is DD103's `unique case` lesson again,
> and it is worse here.

## The argument this course is built on

You are about to be handed **SimProc**: a real 8-bit processor, about 1,200 lines of
SystemVerilog, written by students on this team, wrapped for a real chip. Registers, an ALU,
a memory, a UART you can talk to. It is a genuine piece of hardware design and there is
nothing toy about it.

It shipped with **one test.** Here it is, in full — `test/test.py` from the SimProc
repository, and this is the entire file's content once you strip the boilerplate:

```python
dut.ui_in.value = 1
dut.uio_in.value = 0
await ClockCycles(dut.clk, 100)
assert dut.uo_out.value == 3
```

Set one input pin high, wait a hundred clocks, check the output byte equals 3. Decode `3`
against the chip's pin map — `uo_out[0]` is the UART transmit line, `uo_out[1]` is `halt`,
`uo_out[2]` is `done`:

```
uo_out = 0b00000011
           │      └── uart_tx = 1   the serial line is idle
           │     └─── halt    = 1   the core is sitting in its IDLE state
           │    └──── done    = 0   no instruction has completed
```

**It asserts that the processor is not running.** It sends no command, loads no program,
executes no instruction, and never once looks at a register, a flag, or a byte of memory.

That is not a strawman written for this course. That is the real file, and it is green, and
for a long time it was the only evidence anybody had.

**And the file says so itself.** Two lines above that assertion, in the original, untouched:

```python
    # The following assersion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
    assert dut.uo_out.value == 3
```

That is the project template's own comment, typo and all, still sitting there. Nobody
overrode a warning or ignored a failure. The placeholder simply stayed a placeholder, the
tick stayed green, and there was never a moment where anything went wrong. **That is what
this failure mode looks like from the inside, and it is why it is so common.** Almost every
first tapeout looks like this.

## Thirteen broken processors, one test, thirteen passes

DD104 ships thirteen deliberately broken versions of SimProc. Each one is a **single-line
edit**: `SUB` computes `B - A`; `NAND` is wired as `NOR`; the zero flag only looks at the
bottom four bits; branches sign-extend the wrong way; `LOAD` reads through the destination
register instead of the pointer.

Run the shipped test against all fourteen cores — the good one and the thirteen broken ones:

```bash
cd labs/common
make shuttle
```

```
========================================================================
 THE TEST THIS CHIP SHIPPED WITH
========================================================================
 test/test.py, from the SimProc repository, untouched. It sets
 ui_in = 1, waits 100 clock cycles, and asserts uo_out == 3.
 Decoded: uart_tx = 1 (idle), halt = 1 (IDLE), done = 0.
 It asserts that the processor is NOT RUNNING.
------------------------------------------------------------------------
    PASS  the golden core                              2.8s
    PASS  B01_sub_operands_swapped                     1.3s
    PASS  B02_nand_is_nor                              1.4s
    PASS  B03_zero_flag_low_nibble                     1.4s
    PASS  B04_alu_writeback_reg_field                  1.5s
    PASS  B06_shift_amount_one_bit                     1.6s
    PASS  B07_load_address_from_ra                     1.4s
    PASS  B05_branch_offset_zero_extended              1.4s
    PASS  B09_branch_clobbers_flags                    1.3s
    PASS  B08_store_drops_done                         1.4s
    PASS  B13_store_falls_to_idle                      1.3s
    PASS  B10_ori_adds_instead_of_ors                  1.3s
    PASS  B11_ori_writes_r1_reads_r0                   1.3s
    PASS  B12_uart_rx_bit_period                       1.3s
------------------------------------------------------------------------
 13 of 13 deliberately broken processors pass the
 only test this chip has.
========================================================================
```

Around twenty seconds of wall clock — the per-core figures above are from one run and
yours will differ by a few seconds either way. The sentence at the bottom is the course in
one line:

**The only test this chip has, passes on a processor whose `SUB` is backwards.**

Thirteen out of thirteen is not bad luck. It is what happens when a test's stimulus never
reaches the thing it is supposed to be testing. The test spends its hundred clock cycles
watching a processor sit still, and every one of those thirteen bugs lives somewhere the
processor only goes when it is running.

## Why this is a discipline and not a chore

Here is the economic shape of it, and it is unlike anything in software.

| Where the bug is found | What it costs |
|---|---|
| in simulation | an edit and a re-run — **about eight seconds** |
| in FPGA bring-up | a re-synthesis and a lab afternoon |
| in silicon | a new mask set: months and a great deal of money |
| in silicon, in a product | a recall, or a customer working around your bug forever |

Each row is roughly a hundred times the one above it. That ratio is why "pre-silicon
verification" is a job title, why verification engineers outnumber design engineers on most
commercial chip teams, and why the discipline has its own vocabulary, its own tools, and its
own idea of what counts as evidence.

And what counts as evidence is the part worth taking away. In this field, **a passing test is
not evidence until you know what it would have caught.** A green tick is a claim, and the
claim it makes is exactly as large as the stimulus behind it — which for `test/test.py` is
"this chip powers up idle".

## The reflex

You will hear a version of this on every page of this course, but it starts here:

> **When a test passes, ask what it would have caught.** If you cannot name a specific bug
> that would turn it red, you have not learned anything from the green.

The mechanical form of that question is the one DD104 uses everywhere: run your test against
a design you know is broken. Every lab package here does that automatically, with `make
check`, and it will not give you a passing verdict until your testbench has both passed the
good core **and** failed a broken one.

Two-sided or nothing. That is what a result looks like.

## Try this

Before you go on, spend two minutes with the file itself:

```bash
cd labs/common
cat test_shuttle.py
```

It is the shipped test, untouched, with a comment block explaining the pin decode. Read it
and try to write down — in one sentence, in English — the strongest true claim it supports.

The honest answer is *"after reset and 100 clock cycles with `ui_in[0]` high, this design
drives `uo_out` to `0x03`."* That is a real claim. It is even a useful one; it would catch a
core that came up running by accident, or a UART that transmitted garbage at power-on. It is
just an extremely small claim, and nothing about the way it is written tells you so.

**Every test you write for the rest of your career supports exactly one claim of that shape.
The skill is knowing how big yours is.**

Next: [What a testbench actually is](guide/what-a-testbench-is.md) — the second circuit, whose job
is doubt.
