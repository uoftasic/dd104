# Two simulators, two jobs

**Question this page answers:** *Why does this course ship two simulators, and which one should I be running?*

Both. Not at the same time, and not for the same reason.

Every lab in DD104 runs on **Icarus Verilog** unless you say otherwise, and every lab also
accepts `SIM=verilator`. That is not indecision. The two tools are good at different things,
and by the end of this page you will be able to say which one to reach for without guessing.

Here is the sentence people repeat, and it is wrong: *"Verilator is the fast one."* Here is
what a measurement says.

> Every command below runs in `labs/common`, the shared harness directory
> [Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md) introduces. You have not been
> there yet and you do not need to have been: it runs with `make` alone from a clone of the
> repository, with no environment setup and nothing to configure. Run the commands as you read
> them.

## The same six tests, twice

```bash
cd labs/common
make clean && make sim SIM=icarus
make clean && make sim SIM=verilator
```

Both runs execute [`test_example.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_example.py)
against the golden core. Both pass. Here is the last line of each results table:

```
icarus     ** TESTS=6 PASS=6 FAIL=0 SKIP=0     512010.01     4.38     116812.47 **
verilator  ** TESTS=6 PASS=6 FAIL=0 SKIP=0     512010.01     1.92     267302.99 **
```

Three numbers, and each one means something different.

**`512010.01` is simulated time, in nanoseconds, and it is identical.** Not close — identical,
to the hundredth of a nanosecond, every run, on both tools. The design is the same state
machine either way. A cycle count you measure under one simulator is valid under the other,
which is why every timing number in this course is quoted without saying which tool produced
it.

**`4.38` versus `1.92` is how long the simulator spent simulating.** Verilator did the same
work in **44 %** of the time. Over three runs each I measured Icarus at 4.38 / 4.57 / 4.71 s
and Verilator at 1.90 / 1.92 / 1.97 s, so this is a stable **2.3×**, not a lucky run.

**And here is the number that decides it.** Wall clock, measured with `time` around the whole
`make`, from a clean directory:

| | wall clock | of which simulating | the rest is |
|---|---|---|---|
| Icarus | **6.8 / 5.8 / 5.9 s** | 4.4–4.7 s | starting `vvp`, loading Python |
| Verilator | **16.3 / 16.4 / 16.0 s** | 1.9–2.0 s | **building a C++ program** |

Verilator simulates 2.3× faster and *loses this race by ten seconds*, because it is not really
a simulator in the same sense. It is a **compiler**. It reads your SystemVerilog and emits C++,
and then `g++` has to turn that into a binary before a single clock edge happens. Icarus reads
your SystemVerilog into a bytecode file and starts.

> This is where an intuition from software is about to betray you. "Compiled is faster than
> interpreted" is true *per unit of work*, and it says nothing about a job small enough that
> the compile dominates. You already know this about C++ versus Python for a ten-line script.
> It is exactly the same trade, and simulated time is the unit of work.

## The build cost, measured precisely

Verilator itself is not slow. It is nearly instant:

```
- Verilator: Walltime 0.035 s (elab=0.003, cvt=0.022, bld=0.000)
```

Thirty-five milliseconds to read 1,178 lines of SystemVerilog and write six C++ files.
Everything else is `g++`. You can watch the compiler cache prove it — run the same build twice
inside one container, checking `ccache` in between:

```bash
make clean && make sim SIM=verilator > /dev/null && ccache -s | grep Hits
make clean && make sim SIM=verilator > /dev/null && ccache -s | grep Hits
```

**What you should see:**

```
  Hits:               0 /   6 ( 0.00%)      <- first build: 16.04 s
  Hits:               6 /  12 (50.00%)      <- second build: 3.60 s
```

Six C++ files, six cache misses, sixteen seconds. Six hits, three and a half. **The fifteen
seconds is g++ and nothing else**, and it is paid once per container session, not once per
run — the cache lives inside the container, so it survives `make clean` and dies when the
container does.

**Why an engineer cares:** the honest version of "Verilator is slow to start" is *"the first
build in a fresh container costs about fifteen seconds of g++"*. If you launch the workbench
once in the morning and work inside it, you pay that once. If you spawn a container per
command, you pay it every time. Which of those you do changes the right answer, and nobody
will tell you that in a tool comparison.

## Where the crossover actually is

The trade is: **a fixed build cost versus a per-nanosecond simulation cost.** So the question
is not "which tool is faster", it is "how much simulated time is in this run".

DD104 ships a testbench that is deliberately long —
[`test_values_only.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_values_only.py),
1,889,970 ns of simulated time, 3.7× the example:

```bash
make clean && make sim TB=test_values_only SIM=icarus
make clean && make sim TB=test_values_only SIM=verilator
```

| simulated time in the run | Icarus wall | Verilator wall (cold) | Verilator wall (warm cache) |
|---|---|---|---|
| `test_example` — 512,010 ns | **5.8–6.8 s** | 16.0–16.4 s | 3.2–3.6 s |
| `test_values_only` — 1,889,970 ns | 22.5 s | **22.4 s** | **8.5 s** |

At half a millisecond of simulated time Icarus wins by ten seconds. At two milliseconds they
tie on a cold cache, and Verilator wins by 2.6× on a warm one. The crossover on this design is
somewhere just under **2 ms of simulated time**, and it moves left every time you run again in
the same container.

One more, because it is the case that surprises people. `make check-all` builds and runs
fourteen separate cores — Verilator's worst case, fourteen builds:

```
  Icarus     77.18 s      10 of 13 caught
  Verilator  84.94 s      10 of 13 caught
```

Fourteen full C++ builds and it is still within 10 %, because `ccache` catches most of the
files that do not change between cores. Same verdict, both times, which is the point.

## The half that is not about speed at all

Run this, and read the numbers rather than waiting for them:

```bash
verilator --lint-only --timescale 1ns/1ps --top-module tb \
  rtl/tt_um_ieeeuoftasic_simproc.sv rtl/simproc_system.sv rtl/tb.v
```

**What you should see:** twelve warnings, in **0.077 seconds**, ending with

```
%Error: Exiting due to 12 warning(s)
```

Five of the twelve say `Bit extraction`, and four of those five are the same finding at four
lines of the same module:

```
%Warning-WIDTHTRUNC: rtl/simproc_system.sv:848:16: Bit extraction of array[63:0] requires
                     6 bit index, not 8 bits.
```

`dp_ram` has **64 entries**; the address bus is **8 bits**. Addresses 64–255 are off the end of
the array. Verilator found that by reading the file, before simulating anything, in less time
than it takes to read this sentence. **Icarus compiles the same file and says nothing about
it** — it emits twenty-eight `sorry:` notes about something else entirely and exits 0 (see
[Output that is not an error](reference/output-that-is-not-an-error.md)).

Now watch what each tool does with that defect *at run time*. This ships complete as
[`labs/common/test_two_simulators.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_two_simulators.py):

```bash
cd labs/common
make sim TB=test_two_simulators SIM=icarus
make sim TB=test_two_simulators SIM=verilator
```

The test writes `0x5A` into address 36, then reads address 36 and address 100 out through the
chip's UART and prints the raw bits that came off the pin.

**What you should see** — Icarus:

```
READ  36  (in range)      -> 01011010
READ 100  (off the end)   -> XXXXXXXX
```

and Verilator:

```
READ  36  (in range)      -> 01011010
READ 100  (off the end)   -> 01011010
```

Both tests **pass**. Both runs simulate exactly 60,520.00 ns. And they disagree about what the
chip did.

**Icarus is a 4-state simulator.** Every bit is `0`, `1`, `x` or `z`. Reading past the end of
the array yields `x`, the `x` propagates through the read port and the UART, and eight `X`
characters come out of the chip. That is loud and correct — *if* your stimulus happens to read
address 100.

**Verilator is a 2-state simulator.** There is no `x` in its world; every bit is 0 or 1. The
address was truncated to the six bits the array actually has, `100 & 63 = 36`, and you got the
byte at address 36 — the same `0x5A` you put there. A plausible, silent, wrong answer.

Neither tool is broken. They are answering different questions, and the arithmetic closes
exactly: 100 − 64 = 36.

**Why an engineer cares:** this is not a curiosity, it is a rule about when to trust a green
run. A design that reads uninitialised state, or indexes past an array, or leaves a signal
undriven, will often *work perfectly* under Verilator and produce X under Icarus. Run the same
suite on both and a disagreement is a finding. There is no other way to get that finding out of
a passing test.

## So: which one

| you are | use | because |
|---|---|---|
| editing a test and re-running it every ninety seconds | **Icarus** | no build; six seconds from save to verdict |
| running a long suite, or the same design many times in one session | **Verilator** | 2.3× on simulated time, and the build is already cached |
| about to trust a green run | **both** | the disagreement is the finding |
| looking for width, truncation and case-coverage mistakes | **`verilator --lint-only`** | 0.077 s, and it never needs a testbench |
| chasing an `X` on a pin | **Icarus** | Verilator has no X to show you |
| in a CI job that runs everything once | either | 77 s vs 85 s here — pick on lint, not on speed |

Icarus is the default in [`sim.mk`](https://github.com/uoftasic/dd104/blob/main/labs/common/sim.mk)
for the first row of that table and no other reason. It is not the better simulator. It is the
better *edit-run loop*, which is where you will spend this entire course.

## The one gotcha in switching

`sim.mk` passes `-Wno-fatal` when `SIM=verilator`, and without it Verilator refuses to build
this design at all:

```
%Error: Exiting due to 12 warning(s)
```

Those are the same twelve warnings the lint run prints. Verilator treats warnings as fatal by
default, which is a reasonable policy for code you own and an impossible one for code you have
been handed to test. **Do not read `-Wno-fatal` as "the warnings do not matter."** Read it as
"this design does not lint clean, that is a finding, and the finding is Lab 2's."

## Try this

Prove to yourself that the simulated time really is identical, on your machine, without
reading it off a table. cocotb writes a JUnit XML file with one `sim_time_ns` per test; run
both simulators and diff those numbers alone:

```bash
cd labs/common
make sim TB=test_example SIM=icarus    >/dev/null 2>&1 && cp build/results.xml /tmp/ic.xml
make sim TB=test_example SIM=verilator >/dev/null 2>&1 && cp build/results.xml /tmp/vl.xml
diff <(grep -o 'sim_time_ns="[^"]*"' /tmp/ic.xml) \
     <(grep -o 'sim_time_ns="[^"]*"' /tmp/vl.xml) && echo "identical -- every test, both simulators"
```

**What you should see:** no diff output at all, then the word `identical`. The six values are

```
sim_time_ns="13680.0"
sim_time_ns="11220.0"
sim_time_ns="33370.0"
sim_time_ns="99580.0"
sim_time_ns="33820.0"
sim_time_ns="320340.0"
```

Now do the same with your own testbench. **If a simulated-time number differs, stop.** That
means your testbench depends on something the two tools model differently — almost always an
X, an undriven signal, or a race between two things scheduled in the same delta — and one of
the two green results is not telling you about the design.

Next: [SimProc in one page](guide/simproc-in-one-page.md), where the design under test stops
being a counter and starts being a processor. Or go straight to
[Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md), which is where the twelve
warnings above become a lab.
