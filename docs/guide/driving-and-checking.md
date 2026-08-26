# Driving and checking a design

**Question this page answers:** *My testbench passes. Is that good?*

No. On its own it is not even information.

SimProc shipped with exactly one test. It sets `ui_in = 1`, waits 100 clock cycles, and asserts
`uo_out == 3`. Decoded against the pin map, `3` is `uart_tx = 1` (an idle serial line),
`halt = 1` (the core sitting in `IDLE`) and `done = 0` — **it asserts that the processor is not
running.** It passes on the real core. It also passes on all thirteen deliberately broken cores
in this course's catalogue, including the one whose `SUB` computes `B − A`.

So a passing testbench is a claim about your testbench, not about the design. The claim you
actually want is two-sided:

> It passes on the design that is right, **and** it fails on the design that is wrong.

That is what `make` in this lab checks, and it is why the lab ships a broken counter.

```bash
cd labs/cocotb-intro
make
```

```
------------------------------------------------------------------------
 VERDICT
------------------------------------------------------------------------
   test_03_checking.py PASSED on rtl/counter.sv
   test_03_checking.py FAILED on rtl/counter_broken.sv

   Both halves matter. A testbench that only passes has not been
   shown to be able to fail, and a testbench that cannot fail is
   not evidence of anything.
------------------------------------------------------------------------
```

Four simulator runs, nineteen tests, 0.3 s of simulation. Wall clock is 8–14 s depending on
how busy the machine is.

## The two counters

`rtl/counter_broken.sv` differs from `rtl/counter.sv` by two characters:

```systemverilog
good:    assign tc = en & (q == 8'hFF);
broken:  assign tc =       (q == 8'hFF);
```

**Every value of `q` is still correct**, on every cycle, from every starting point, forever.
The count is perfect. Only `tc` is wrong, and only while `en` is low.

That is the shape of a real bug, and it is worth sitting with for a second. Most bugs are not
"the design is broken". Most bugs are "one output is wrong in one situation nobody tests".

## Six tests, and what each is for

[`test_03_checking.py`](https://github.com/uoftasic/dd104/blob/main/labs/cocotb-intro/test_03_checking.py)
in full is six tests. Their names are the argument:

| test | what it is for | catches the `tc` bug? |
|---|---|---|
| `load_then_count` | the ordinary path — load a value, count eight times | no |
| `enable_holds_the_count` | the case where the design must do **nothing** | no |
| `load_wins_over_enable` | priority between two controls that are both asserted | no |
| `terminal_count_needs_enable` | `tc` at `q = 0xFF` with `en` **low** | **yes, every time** |
| `the_wrap_is_where_the_bugs_live` | the exact cycle 255 → 0, `(q, tc)` pairs | no |
| `against_a_reference_model` | 600 random clocks against six lines of Python | no |

Five of six pass on the broken counter. **Including the 600-clock random test.**

## The three test shapes worth stealing

**Test the case where the answer is "nothing happens."** `enable_holds_the_count` drives
`en = 0` and clocks twenty times, then checks the count did not move. Half of any specification
is the half where the design must hold still, and almost nobody writes a test for it.

**Test priority explicitly.** `load_wins_over_enable` raises `load` and `en` together. Somebody
has to win, and which one wins lives in the *order* of two `else if` branches — exactly the kind
of thing an editor reorders while tidying, with no warning from any tool.

**Test the output nobody looks at.** That is what `terminal_count_needs_enable` is, and it is
the only test in the file that catches the bug. Flags, status bits, `done` pulses, `valid`
lines: these are architectural state exactly as much as a data value is, and a testbench that
only ever checks data cannot see a flag bug. Not "is unlikely to" — **cannot**.

## An assertion that says something useful

Compare. Here is the assertion most people write:

```python
assert dut.tc.value == 0
```

and here is the one in the lab:

```python
assert tc == 0, (
    f"q is 0xFF and en is 0, so the count is NOT about to wrap, but tc is {tc}.\n"
    f"  tc should be `en & (q == 8'hFF)`. A tc of 1 here means the `en &`\n"
    f"  is missing and tc is really just `q == 8'hFF`.\n"
    f"  Everything about the COUNT is still correct -- only the flag is wrong,\n"
    f"  and only while en is low.\n  {state(dut)}")
```

`make broken` prints it:

```
   404.00ns WARNING  ..able.terminal_count_needs_enable q is 0xFF and en is 0, so the count is NOT about to wrap, but tc is 1.
                                                            tc should be `en & (q == 8'hFF)`. A tc of 1 here means the `en &`
                                                            is missing and tc is really just `q == 8'hFF`.
                                                            Everything about the COUNT is still correct -- only the flag is wrong,
                                                            and only while en is low.
                                                            q=0xFF tc=1 en=0 load=0 rst_n=1 at t=404 ns
                                                        assert Logic('1') == 0
```

Read that and you know the line of RTL to open. You did not re-run anything, add a print, or
open a waveform. **That is the standard.** The rule of thumb: *write the message you would want
if this failed at 2 a.m. six months from now, on someone else's machine.*

Three habits get you there:

**A `state()` helper, pasted into every message.**

```python
def state(dut):
    return (f"q=0x{int(dut.q.value):02X} tc={dut.tc.value} "
            f"en={dut.en.value} load={dut.load.value} "
            f"rst_n={dut.rst_n.value} at t={get_sim_time('ns'):.0f} ns")
```

One line, every input and output, and the time. Write it once per design.

**Say what each possible wrong answer would mean.**

```python
assert got == 0x11, (
    f"with load AND en both high, q became 0x{got:02X}.\n"
    f"  0x11 means load won (correct for this design).\n"
    f"  0x12 means load won and en also applied.\n"
    f"  anything else means en won.\n  {state(dut)}")
```

Now the failure is not "it was wrong", it is a diagnosis you wrote before you needed it.

**Report differences, not just values.** `expected 0x35, got 0x36 — a difference of +1` is a
sentence that names the bug. `expected 0x35, got 0x36` makes the reader do subtraction at 2 a.m.

## Two things that pass and should not comfort you

**Comparing a whole sequence beats comparing one value.** `the_wrap_is_where_the_bugs_live`
collects five `(q, tc)` pairs and compares the list in one assertion, so the failure shows the
whole trajectory:

```
   486.00ns INFO  cocotb.counter  q, tc across the wrap: (254,0) (255,1) (  0,0) (  1,0) (  2,0)
```

**Random stimulus finds bugs by accident.** `against_a_reference_model` runs 600 clocks against
a six-line Python model of the counter, checking `q` and `tc` on every one. It is the most
thorough test in the file and it **passes on the broken counter**, and the test says so itself:

```
  6507.01ns INFO  cocotb.counter  600 random clocks, q and tc agreed with the model on every one (final q = 0x7C)
  6507.01ns INFO  cocotb.counter  of those 600 clocks, 0 had q = 0xFF with en low -- the only ones where a broken tc would have shown
```

**Zero.** In 600 clocks of random stimulus, the one situation that exposes the bug never
occurred once — because the counter only reaches `0xFF` while it is running, and while it is
running the broken `tc` and the correct `tc` agree.

The seed is pinned (`random.Random(104)`) so that number means the same thing on your machine as
it does on this page. Un-pin it and you get a test that passes on Tuesday and fails on
Wednesday, and no way to tell whether you changed the design or drew a different hand.

**Reflex check:** when a random or constrained-random test passes, ask *"how many of those
vectors actually reached the situation I care about?"* and then count it — a counter in the loop
and one extra log line. If the answer is zero, the test told you nothing about that situation,
however many vectors it ran. **Do not mistake volume for coverage.**

## What a reference model is

Six lines:

```python
if load:      model_q = d
elif en:      model_q = (model_q + 1) & 0xFF
model_tc = 1 if (en and model_q == 0xFF) else 0
```

Written from the specification, in a different language, by someone who is allowed to be lazy
about *how*. It is worth having because it checks the things you did not think to check — a
directed test looks at one signal at a time, but a model looks at all of them, on every cycle.

Its limitation is exactly as important as its power: **the model can only be wrong in the same
way you are.** This one has no idea `tc` should depend on `en` in any situation the stimulus
did not reach, and it has no idea `done` or `halt` exist at all. In SimProc that gap is a whole
class of bug — a core that computes every answer correctly and gets its handshake wrong sails
straight through a model comparison.

That is not a flaw in model-based testing. It is the reason a suite needs more than one kind of
test in it.

## Try this

Make the good counter fail. Open `rtl/counter.sv` and change

```systemverilog
else if (en)     q <= q + 8'd1;
```

to `q <= q + 8'd2`, then run:

```bash
make sim
```

**What you should see:** `load_then_count` fails first, on the very first comparison:

```
    31.00ns WARNING  .. load_then_count.load_then_count counting from 0x30: expected 0x31, got 0x32 -- a difference of +1
                                                            q=0x32 tc=0 en=1 load=0 rst_n=1 at t=31 ns
                                                        assert 50 == 49
```

The difference `+1` is the diagnosis, and `q=0x32 ... at t=31 ns` tells you it happened on the
very first counted edge rather than drifting in later. (`assert 50 == 49` is pytest showing the
same numbers in decimal — see the [first page](guide/your-first-cocotb-test.md) on assertion
rewriting.)

`the_wrap_is_where_the_bugs_live` fails too, and its message shows the whole trajectory
`[(255, 1), (1, 0), (3, 0), (5, 0), (7, 0)]` — the counter stepping by two. Two failures, two
different views of one bug. Undo the edit; `make sim` is green again.

**Why an engineer cares:** you have now watched your own testbench catch a bug you planted, in
a design you understand, in eight seconds. Everything in
[Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md) onward is that, on a processor,
with bugs somebody else planted.

Next: [Waveforms when the assertion is not enough](guide/waveforms.md).
