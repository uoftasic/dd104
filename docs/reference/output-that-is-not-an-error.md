# Output that is not an error

**Question this page answers:** *The screen is full of red and yellow. Did something break?*

Mostly no. This page names every wall of scary output DD104 produces, gives you the exact count
so you can confirm you are seeing the same thing, and — for each one — the **one-line rule** that
tells it apart from a real failure.

Read it before you meet them. An asynchronous course dies of *"is this bad?"*, and the answer is
cheaper to give in advance than to find at 2 a.m.

The rules, up front:

| tool | it is fine when | it is real when |
|---|---|---|
| Icarus compile | lines say `sorry:`, exit code **0** | a line starts `error:`, and compilation **stops** |
| Verilator | you passed `-Wno-fatal` and the build finished | it says `%Error:` **and no binary was produced** |
| cocotb | `TESTS=n PASS=n FAIL=0` | `FAIL` is non-zero, **or the results table is missing entirely** |
| `make check` | `VERDICT: PASS` | `VERDICT: FAIL` — and `make: *** Error 1` under it is the verdict talking |

---

## 1. Icarus prints 28 lines saying `sorry:`

Compile the design the way the labs do:

```bash
cd labs/common/rtl
iverilog -g2012 -o /tmp/sp.vvp tt_um_ieeeuoftasic_simproc.sv simproc_system.sv tb.v
```

**What you should see:** twenty-eight lines like this, and nothing else.

```
simproc_system.sv:552: sorry: constant selects in always_* processes are not fully
supported (the process will be sensitive to all bits in 'instr_reg_out[7:0]').
```

Confirm the count yourself:

```bash
iverilog -g2012 -o /tmp/sp.vvp tt_um_ieeeuoftasic_simproc.sv simproc_system.sv tb.v > /tmp/ic.log 2>&1
echo "exit code: $?"                       # run it UNPIPED, or you get grep's exit code
grep -c 'sorry:' /tmp/ic.log               # 28
grep -c 'error:' /tmp/ic.log               # 0
wc -l < /tmp/ic.log                        # 28 -- there is nothing else
grep -oE '^[^ ]+:[0-9]+:' /tmp/ic.log | sort -u | wc -l    # 22 distinct locations
```

> Note the shape of that block, because the course keeps making the same point about its own
> instructions: **`$?` after a pipeline is the exit code of the last command in the pipeline.**
> Write `cmd > file 2>&1` and check `$?` on its own line, then grep the file. `cmd | grep -c ...`
> turns a compiler failure into a plausible-looking count of zero.

| | |
|---|---|
| `sorry:` lines | **28** |
| distinct source locations | **22** (six lines produce two each) |
| total lines of output | **28** — there is nothing else |
| `error:` lines | **0** |
| `warning:` lines | **0** |
| exit code | **0** |

**These are notes, not warnings.** Icarus is telling you that where you wrote `instr_reg_out[3:0]`
inside an `always_comb`, it will make the process sensitive to **all eight bits** instead of just
the four you selected. That is *more* sensitivity, not less: the block re-evaluates more often
than strictly necessary and the simulation is correct. Every one of the 22 locations is in the
decoder, between lines 543 and 677, which is exactly where a processor slices an instruction
word into fields.

> **The rule:** *a real Icarus failure starts a line with `error:` and stops.* `sorry:` is
> Icarus saying "I am doing this a less clever way"; `error:` is Icarus saying "I am not doing
> this".

For contrast, here is a real one. Drop `-g2012` — the flag that turns on SystemVerilog-2012 —
and the same three files produce:

```
simproc_system.sv:122: syntax error
simproc_system.sv:122: error: Invalid module instantiation
```

| | with `-g2012` | without it |
|---|---|---|
| lines of output | 28 | **414** |
| `error:` lines | 0 | **288** |
| exit code | 0 | **152** |
| `/tmp/sp.vvp` | written | **not written** |

Nothing subtle about the difference. If you ever see `syntax error` on a line of perfectly good
SystemVerilog, the missing flag is `-g2012`, and `sim.mk` already passes it.

---

## 2. Verilator prints 12 warnings and refuses to build

```bash
cd labs/common
verilator --lint-only --timescale 1ns/1ps --top-module tb \
  rtl/tt_um_ieeeuoftasic_simproc.sv rtl/simproc_system.sv rtl/tb.v
```

**What you should see:** twelve warnings in **0.077 seconds**, then

```
%Error: Exiting due to 12 warning(s)
```

Exit code 1. Count them by kind:

```bash
verilator --lint-only --timescale 1ns/1ps --top-module tb \
  rtl/tt_um_ieeeuoftasic_simproc.sv rtl/simproc_system.sv rtl/tb.v > /tmp/v.log 2>&1
grep '^%Warning' /tmp/v.log | sed 's/^%Warning-\([A-Z]*\).*/\1/' | sort | uniq -c
```

```
      2 CASEINCOMPLETE
      4 WIDTHEXPAND
      6 WIDTHTRUNC
```

**Five of the twelve say `Bit extraction`, and they are the only ones that are findings rather
than tidiness.**

| line | module | what it says |
|---|---|---|
| `simproc_system.sv:848` | `dp_ram` | `Bit extraction of array[63:0] requires 6 bit index, not 8 bits` |
| `simproc_system.sv:851` | `dp_ram` | same, the other write port |
| `simproc_system.sv:856` | `dp_ram` | same, read port A |
| `simproc_system.sv:857` | `dp_ram` | same, read port B |
| `simproc_system.sv:1022` | `UART_RX` | `Bit extraction of var[7:0] requires 3 bit index, not 4 bits` |

Four of the five are one defect at four lines: **the RAM has 64 entries and the address bus is
8 bits wide**, so addresses 64–255 are off the end of the array. Verilator found that by reading
the file, before simulating anything. Icarus never mentions it and shows it to you at run time
as eight X bits on a pin — *if* your stimulus happens to read address 100. That is
[Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md), and the run-time half is
measured in [Two simulators, two jobs](guide/two-simulators-two-jobs.md).

**Why it refuses to build.** Verilator treats warnings as fatal by default. That is a reasonable
policy for code you own and an impossible one for code you have been handed to test, so
[`sim.mk`](https://github.com/uoftasic/dd104/blob/main/labs/common/sim.mk) passes `-Wno-fatal`
when `SIM=verilator`. You will see the same twelve warnings scroll past during a normal
`make sim SIM=verilator` and then the build finishes.

> **The rule:** *with `-Wno-fatal`, `%Error: Exiting due to N warning(s)` at the end of a build
> that produced a binary is scenery. Without it, no binary was produced and nothing ran.* Check
> for the results table, not for the word `Error`.
>
> And do **not** read `-Wno-fatal` as "the warnings do not matter." Read it as *"this design
> does not lint clean, that is a finding, and the finding is Lab 02's."*

### `-Wall` gives 19, and 27 if you include the testbench

```bash
verilator --lint-only -Wall --timescale 1ns/1ps \
  --top-module tt_um_ieeeuoftasic_simproc \
  rtl/tt_um_ieeeuoftasic_simproc.sv rtl/simproc_system.sv
```

**The design alone, `-Wall`: 19.**

| kind | count | is it a finding? |
|---|---|---|
| `WIDTHTRUNC` | 6 | yes — the five `Bit extraction` plus one packet-width slip |
| `WIDTHEXPAND` | 4 | no — `index <= 1'b0` assigning 1 bit to a 4-bit register |
| `UNUSEDSIGNAL` | 4 | no |
| `CASEINCOMPLETE` | 2 | worth a look — an incomplete `case` is how latches and X get in |
| `UNUSEDPARAM` | 1 | no |
| `PINCONNECTEMPTY` | 1 | no |
| `DECLFILENAME` | 1 | no — the module is not named after its file |

6 + 4 + 4 + 2 + 1 + 1 + 1 = **19**.

Add the course's `rtl/tb.v` and the same command reports **27**. The extra eight are 5 `UNDRIVEN`
and 3 `UNUSEDSIGNAL`, **all of them inside `tb.v`** — which is a testbench wrapper with pins it
deliberately does not drive. 19 + 8 = 27, and the arithmetic closing is the check that you have
not accidentally found something new.

> **The rule for `-Wall` output generally:** *sort it by warning kind and look at the width and
> case ones first.* `WIDTHTRUNC` and `CASEINCOMPLETE` describe the design doing something you did
> not write. `UNUSED*`, `DECLFILENAME` and `PINCONNECTEMPTY` describe the design not being tidy.

### One more you can cause by accident

Leave `--timescale 1ns/1ps` off the lint command and you get **ten extra** `TIMESCALEMOD`
warnings — one per module — because `tb.v` has a timescale and the RTL files do not. cocotb's
own makefiles pass `--timescale`, so you only ever see this when you run `verilator` by hand.
Ten warnings that appeared because of your command line, not because of the design.

---

## 3. cocotb's yellow: deprecation warnings

`WARNING` in a cocotb log is a log level, not a verdict. The ones you will actually see:

```
0.00ns WARNING  py.warnings  .../test.py:24: DeprecationWarning: The 'units' argument
                             has been renamed to 'unit'.
0.00ns WARNING  py.warnings  DeprecationWarning: `logic_array.integer` getter is
                             deprecated. Use `logic_array.to_unsigned()` instead.
               Using MODULE is deprecated, please use COCOTB_TEST_MODULES instead.
```

**All three of those still work.** The test runs, the test passes, the log is noisier. cocotb
2.0.1 accepts `units=`, `MODULE=` and `.integer`, does the right thing, and warns.

> ⚠ **Do not go hunting for a failure that is not there.** Any page telling you that `MODULE=`
> causes a silent no-test run is wrong; it has been measured in this container and it works,
> with a warning. Write the new spellings anyway — a deprecation is a countdown — but a
> `DeprecationWarning` is not why your test is failing.
>
> The three that *are* hard errors: `cocotb.fork` → `AttributeError`, `@cocotb.coroutine` →
> `AttributeError`, `dut.sig <= 1` → `TypeError`. Four runnable demonstrations ship in
> [`labs/cocotb-intro/oldapi/`](https://github.com/uoftasic/dd104/tree/main/labs/cocotb-intro/oldapi).
> Full breakdown: [cocotb 2.x vs every tutorial](guide/cocotb-2x-vs-every-tutorial.md).

Other lines that look like problems and are not:

| line | what it is |
|---|---|
| `-.--ns INFO gpi ... VPI registered` | cocotb attaching to the simulator. The `-.--ns` is "before time started". |
| `Seeding Python random module with 1787752037` | the seed for this run, so you can reproduce it |
| `- :0: Verilog $finish` | Verilator's normal end-of-simulation line |
| `sys:1: RuntimeWarning: coroutine '_do_writes' was never awaited` | Python cleaning up after cocotb's writer task at shutdown |

---

## 4. `make: *** Error 1` after a failed verdict

```
 VERDICT: FAIL — your testbench passes B03_zero_flag_low_nibble too.
   A test that passes on a broken core is not testing that core.
========================================================================

  The verdict above is FAIL, so this target exits non-zero and make
  prints an error line under this one. That is the verdict talking,
  not a broken Makefile.
make: *** [lab.mk:66: check] Error 1
```

A failed verdict is a **non-zero exit on purpose**, so the labs are usable from a script or a CI
job without anyone having to grep the text. `make` reports a non-zero exit from anything it
runs. The lab prints the paragraph above it so you know which of the two you are looking at.

> **The rule:** *read the `VERDICT:` line, not the `make:` line.* If there is a `VERDICT:` line,
> the machinery worked.

The same applies to a cocotb test that fails: the results table still prints, `FAIL` is
non-zero, and `make` reports `Error 2` from `Makefile.icarus`. That is the test failing, which is
what you asked it to do.

---

## 5. The dangerous direction: green output that ran nothing

Everything above is noise that looks like failure. These are the opposite, and they are worse.

**`python3 -m pytest test_example.py`**

```
collected 0 items
============================ no tests ran in 0.10s =============================
```

**Exit 0.** It looks like the obvious command. It is green. It ran nothing. A cocotb test is not
a pytest test.

**`python3 test_example.py`**

No output at all. **Exit 0.** A cocotb test is not a Python program either — it needs a simulator
underneath it, and the only thing that starts one here is `make`.

**A typo in `COCOTB_TESTCASE`**

```bash
make sim TB=test_example COCOTB_TESTCASE=chekcing
```

```
0.00ns WARNING  cocotb.regression   No tests left after filtering with: chekcing$
```

**Exit 0**, no results table, and `build/results.xml` contains six `<skipped/>` entries. The
simulator started, cocotb attached, and every test was filtered out by a name that matches
nothing.

> **The rule that covers all three:** *a run that tested something prints a results table ending
> in `TESTS=n PASS=n FAIL=0 SKIP=0`.* No table means no tests ran, whatever the exit code says.
> Check the table, then check that `n` is the number you expected.

That last clause matters. `TESTS=5` when you wrote six is the same failure in a quieter costume.

---

## The whole checklist

Before you conclude a run was fine:

1. Is there a **results table**? No table, no tests.
2. Does `TESTS=n` match the number of `@cocotb.test()` functions you wrote?
3. Is `FAIL=0`?
4. If a verdict target ran, does it say `VERDICT: PASS`?
5. Did the build actually produce something — a `.vvp`, or a `Vtop`?

Nothing on that list is the exit code, and nothing on it is the absence of the word `Error`.

Everything on this page is generated by the harness in
[`labs/common`](https://github.com/uoftasic/dd104/tree/main/labs/common), which is documented
call by call in [The SimProc harness](reference/the-harness-api.md). The design that provokes
most of it is the subject of [Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md).
