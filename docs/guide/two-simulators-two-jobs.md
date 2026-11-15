# Two simulators

This page answers: *why does this course ship two simulators, and which one should I run?*

Both, for different reasons. Every DD104 lab runs on Icarus Verilog unless you say otherwise,
and every lab also accepts `SIM=verilator`. The two tools are good at different things, and by
the end of this page you should be able to say which one to reach for.

People often say "Verilator is the fast one". The measurements below say something more useful.
They were all taken in `labs/common`, the shared harness directory, and you'll repeat the
important ones in [Lab 02, Part 5](../labs/lab-02-the-only-test-this-chip-has-overview.md#part-5-two-simulators).

## The same six tests, twice

`make sim SIM=icarus` and `make sim SIM=verilator` in `labs/common` both run
[`test_example.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_example.py)
against the golden core, and both pass. The last line of each results table:

```
icarus     ** TESTS=6 PASS=6 FAIL=0 SKIP=0     512010.01     4.38     116812.47 **
verilator  ** TESTS=6 PASS=6 FAIL=0 SKIP=0     512010.01     1.92     267302.99 **
```

Each of the three numbers means something different.

`512010.01` is simulated time in nanoseconds, and it is identical on both tools, to the
hundredth of a nanosecond, every run. The design is the same state machine either way, so a cycle
count measured on one simulator holds on the other. That is why the course quotes timing numbers
without saying which tool produced them.

`4.38` against `1.92` is how long each simulator spent simulating. Verilator did the same work in
44 % of the time. Over three runs each, Icarus measured 4.38 / 4.57 / 4.71 s and Verilator 1.90 /
1.92 / 1.97 s, a stable 2.3×.

The number that decides which to use is wall clock, measured with `time` around the whole `make`
from a clean directory:

| | Wall clock | Of which simulating | The rest is |
|---|---|---|---|
| Icarus | 6.8 / 5.8 / 5.9 s | 4.4–4.7 s | Starting `vvp`, loading Python |
| Verilator | 16.3 / 16.4 / 16.0 s | 1.9–2.0 s | Building a C++ program |

Verilator simulates 2.3× faster and loses by ten seconds, because it is a compiler rather than a
simulator in the same sense. It reads your SystemVerilog and emits C++, and `g++` has to turn that
into a binary before the first clock edge. Icarus reads your SystemVerilog into a bytecode file
and starts.

> "Compiled is faster than interpreted" is true per unit of work. It says nothing about a job
> small enough that the compile dominates. You already know this about C++ against Python for a
> ten-line script; this is the same trade, with simulated time as the unit of work.

## The build cost

Verilator itself is nearly instant:

```
- Verilator: Walltime 0.035 s (elab=0.003, cvt=0.022, bld=0.000)
```

That is 35 milliseconds to read 1,178 lines of SystemVerilog and write six C++ files. The rest is
`g++`, and `ccache` shows it. Two Verilator builds in one container, with `make clean` between
them:

```
  Hits:               0 /   6 ( 0.00%)      <- first build: 16.04 s
  Hits:               6 /  12 (50.00%)      <- second build: 3.60 s
```

Six C++ files, six cache misses, sixteen seconds; then six hits, three and a half seconds. The
difference is `g++` and nothing else, and you pay it once per container session, not once per
run. The cache lives inside the container, so it survives `make clean` and is lost when the
container stops.

So the accurate version of "Verilator is slow to start" is that the first build in a fresh
container costs about fifteen seconds of `g++`. If you start the workbench once in the morning and
work inside it, you pay that once. If you start a container per command, you pay it every time.
Tool comparisons rarely mention that, and it changes the answer.

## Where the crossover is

The trade is a fixed build cost against a per-nanosecond simulation cost, so the question is how
much simulated time is in the run. DD104 ships a deliberately long testbench,
[`test_values_only.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_values_only.py),
with 1,889,970 ns of simulated time, 3.7× the example. Measured wall clock:

| Simulated time in the run | Icarus | Verilator, cold cache | Verilator, warm cache |
|---|---|---|---|
| `test_example`: 512,010 ns | 5.8–6.8 s | 16.0–16.4 s | 3.2–3.6 s |
| `test_values_only`: 1,889,970 ns | 22.5 s | 22.4 s | 8.5 s |

At half a millisecond of simulated time, Icarus wins by ten seconds. At two milliseconds they tie
on a cold cache, and Verilator wins by 2.6× on a warm one. On this design the crossover is just
under 2 ms of simulated time, and it moves lower every time you rerun in the same container.

`make check-all` builds and runs fourteen separate cores, which is Verilator's worst case:

```
  Icarus     77.18 s      10 of 13 caught
  Verilator  84.94 s      10 of 13 caught
```

Fourteen full C++ builds, and it is still within 10 %, because `ccache` catches most of the files
that do not change between cores. The verdict is the same both times, which is what matters.

## Lint and X

Verilator also lints. Run on the three SimProc source files with `--lint-only`, it prints twelve
warnings in 0.077 seconds, ending with:

```
%Error: Exiting due to 12 warning(s)
```

Five of the twelve say `Bit extraction`, and four of those five are one finding at four lines of
the same module:

```
%Warning-WIDTHTRUNC: rtl/simproc_system.sv:848:16: Bit extraction of array[63:0] requires
                     6 bit index, not 8 bits.
```

`dp_ram` has 64 entries and the address bus is 8 bits, so addresses 64–255 are off the end of
the array. Verilator found that by reading the file, before simulating anything. Icarus compiles
the same file and says nothing about it; it prints twenty-eight `sorry:` notes about something
else and exits 0 (see [Output that is not an error](../reference/output-that-is-not-an-error.md)).

Now see what each tool does with that defect at run time.
[`labs/common/test_two_simulators.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_two_simulators.py)
writes `0x5A` to address 36, then reads address 36 and address 100 back out through the chip's
UART and prints the raw bits that came off the pin.

Icarus:

```
READ  36  (in range)      -> 01011010
READ 100  (off the end)   -> XXXXXXXX
```

Verilator:

```
READ  36  (in range)      -> 01011010
READ 100  (off the end)   -> 01011010
```

Both runs pass, both simulate exactly 60,520.00 ns, and they disagree about what the chip did.

Icarus is a 4-state simulator: every bit is `0`, `1`, `x` or `z`. Reading past the end of the
array gives `x`, the `x` propagates through the read port and the UART, and eight `X` characters
come out of the chip. That is loud and correct, provided your stimulus happens to read address
100.

Verilator is a 2-state simulator: every bit is 0 or 1. The address was truncated to the six bits
the array has, `100 & 63 = 36`, and you got the byte at address 36, the same `0x5A` you put there.
That is a plausible, silent, wrong answer.

Neither tool is broken. They answer different questions, and the arithmetic closes exactly:
100 − 64 = 36.

This gives you a rule about when to trust a green run. A design that reads uninitialised state,
indexes past an array or leaves a signal undriven will often work perfectly under Verilator and
produce X under Icarus. Run the same suite on both, and a disagreement is a finding you can't get
out of a single passing run.

## Which one to use

| You are | Use | Because |
|---|---|---|
| Editing a test and rerunning it every ninety seconds | Icarus | No build; six seconds from save to verdict |
| Running a long suite, or the same design many times in one session | Verilator | 2.3× on simulated time, and the build is already cached |
| About to trust a green run | Both | The disagreement is the finding |
| Looking for width, truncation and case-coverage mistakes | `verilator --lint-only` | 0.077 s, and it needs no testbench |
| Chasing an `X` on a pin | Icarus | Verilator has no X to show you |
| In a CI job that runs everything once | Either | 77 s against 85 s here; choose on lint, not speed |

Icarus is the default in [`sim.mk`](https://github.com/uoftasic/dd104/blob/main/labs/common/sim.mk)
because of the first row of that table and no other reason. It is not the better simulator. It
has the faster edit-run loop, which is where you'll spend this course.

## `-Wno-fatal`

`sim.mk` passes `-Wno-fatal` when `SIM=verilator`. Without it, Verilator refuses to build this
design:

```
%Error: Exiting due to 12 warning(s)
```

Those are the same twelve lint warnings. Verilator treats warnings as fatal by default, which is a
reasonable policy for code you own and an impossible one for code you have been handed to test.
Don't read `-Wno-fatal` as "the warnings do not matter". Read it as "this design does not lint
clean, and that is a finding". Lab 02 is where you look at it.

## Identical simulated time

cocotb writes a JUnit XML file with one `sim_time_ns` per test. Run both simulators, extract
those values and diff them, and there is no difference. The six values for `test_example` are:

```
sim_time_ns="13680.0"
sim_time_ns="11220.0"
sim_time_ns="33370.0"
sim_time_ns="99580.0"
sim_time_ns="33820.0"
sim_time_ns="320340.0"
```

Do the same with your own testbench. If a simulated-time number differs, stop: your testbench
depends on something the two tools model differently, almost always an X, an undriven signal, or
a race between two things scheduled in the same delta, and one of the two green results is not
telling you about the design.

## Check yourself

1. You will run a 10 µs test fifty times this afternoon in one container. Which simulator, and
   why?
2. A test passes on both simulators but its `sim_time_ns` differs between them. What does that
   suggest?
3. Why can Verilator never show you an `X` on a pin?

Next: [SimProc in one page](../guide/simproc-in-one-page.md).
