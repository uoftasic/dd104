# Getting started

This page covers what DD104 needs from your machine, which tool versions it is pinned to, how
to read the labs' output, and how to get help. You'll do the actual setup in
[Lab 01, Part 1](labs/lab-01-the-adder-you-already-trust-overview.md#part-1-set-up).

## Requirements

You already did the hard part in [IC101](https://uoftasic.com/ic101/), and you have been using
the same container since [DD102](https://uoftasic.com/dd102/). DD104 is the lightest course in
the digital track to set up. There is no PDK, no liberty file, no `STD_CELL_LIBRARY` and no
LibreLane, and nothing in the course is ever mapped to silicon. The whole tool story is a
simulator, Python and a waveform viewer.

The setup has three pieces, all of which you have used before:

- the noVNC desktop, started from your `workspace` clone with `./scripts/start_vnc.sh`
  (ports, passwords and blank-page fixes are in
  [IC101: Launch the noVNC desktop](https://uoftasic.com/ic101/#/guide/launch-novnc));
- `. /foss/designs/common/.designinit`, which in DD104 does one thing for you: it defines the
  `mod` command;
- `mod add dd104`, which clones this repo into `/foss/designs/modules/dd104`. That folder is
  your `workspace` folder bind-mounted into the container, so your files are on your own disk
  and deleting the container does not delete your work.

Every DD104 lab also runs with `make` alone, in a bare container, with no environment setup.
The labs pin their own paths. So if a setup step fails late at night, type `make` anyway and
read what it tells you.

## Versions

The course is pinned to `hpretl/iic-osic-tools:2026.08`. These are the versions it ships:

| Tool | Version |
|---|---|
| Icarus Verilog | `14.0 (devel)` |
| Verilator | `5.050` |
| cocotb | `2.0.1` |
| Surfer | `0.6.0` |

The cocotb version matters most. cocotb 2.0 renamed things that appear in the first few lines
of every 1.x example, and most of what a search engine returns is 1.x. The split is shorter than
you might expect:

- Most 1.x forms still run on 2.0.1 and print a `DeprecationWarning`: `units=` instead of
  `unit=`, `MODULE=` in a Makefile, `sig.value.integer`. Write the new spellings anyway, but
  if your run is red, these are not why.
- Three 1.x forms are hard errors: `cocotb.fork` (use `cocotb.start_soon`),
  `@cocotb.coroutine` (use a plain `async def`), and `dut.sig <= 1` (use
  `dut.sig.value = 1`). None of the error messages mentions a version number.

When a tutorial disagrees with this course, the course is describing the cocotb installed in
your container. The full measured list is
[cocotb 2.x and older tutorials](guide/cocotb-2x-vs-every-tutorial.md).

## Reading a lab's output

Every lab ends with a verdict block, and a failed verdict exits non-zero on purpose so that a
script or CI job can read the result without grepping text. `make` reports that non-zero exit
with a line like this:

```
make: *** [Makefile:49: check] Error 1
```

That line is the verdict talking, not a broken Makefile. The lab prints two lines saying so
just above it. You will see it often, and it goes away when the verdict passes.

Your first run is meant to fail. Lab 01 hands you a testbench that passes on both a good adder
and a broken one, so `make` ends on `VERDICT: FAIL`. That is the starting point of the course.

Lab writeups mark each number as exact or ballpark. Simulated time, vector counts, cycle counts
and verdicts are exact: if one of those does not reproduce on your machine, that is a bug in
the course and we want to hear about it. Wall-clock seconds are ballpark; ±25 % from run to run
is normal.

## How long things take

The image is the same ~19 GB you pulled for IC101, and DD104 adds nothing to it. Measured wall
clock in the pinned container, on a machine that was doing other things:

| Job | Wall time |
|---|---|
| Lab 01 end to end: two tests, against two adders | ~5 s |
| The example testbench against the SimProc core (Icarus) | ~6 s |
| The same six tests under Verilator, including its build | ~17 s (~3 s once built) |
| The shipped chip test against the good core and all 13 broken ones | ~19 s |
| Verilator toggle coverage on the Lab 01 adder, both stimulus sets | ~12 s |

Because runs are this cheap, you can rerun your tests every time you change a line, and the
labs assume you will.

## Getting help

- Ask in the [team Discord](https://discord.gg/hrJnP5UsGz). No question is too basic. Much of
  what looks like your mistake in a verification course is the tool being unhelpful, and in
  this course a lot of it is a design that is supposed to be broken.
- Quote the exact error and say which core you were running against. "My test fails" and "my
  test fails on `B07` and passes on the golden core" are different questions. In a Python
  traceback, the last line is the real error; everything above it is the call stack, most of it
  cocotb's machinery.
- Paste the whole verdict block, not a screenshot of one line. It says which core, which
  testbench and which tests fired, which is most of the diagnosis.
- If a command in a lab does not do what the lab says, report it. Every command was run before
  it was written, so a mismatch means something drifted.

### Requests to avoid

`labs/common/bugs.py` lists all thirteen bugs, in order, with line numbers. So do
`labs/simproc/solutions/bug-NN.md` and `labs/simproc/variants/bug-NN/bug.patch`, which is the
one-line edit itself. They are in your clone and nothing stops you reading them. Reading them
throws away what the course teaches, which is finding a bug you cannot see. You only get to
practise that on bugs you haven't been told about.

If you are stuck, ask in Discord for a better question to ask the design, not for the answer.

Next: [What a passing test proves](guide/it-works-is-not-a-result.md).
