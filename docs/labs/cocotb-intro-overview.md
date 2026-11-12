# Lab: cocotb on a counter

You'll run every cocotb example from the guide pages on an 8-bit counter: your first test, the
clock-edge race, the triggers, the 1.x forms that warn and the ones that fail, a two-sided
verdict, and the counter's waveforms in Surfer and GTKWave. Nothing here is graded. It is
practice with the tools before the processor arrives in Lab 02, and twice you'll break something
on purpose and check that the right tests notice.

This lab takes about 75 minutes.

Package: [`labs/cocotb-intro/`](https://github.com/uoftasic/dd104/tree/main/labs/cocotb-intro)

## Before you start

- Finish [Lab 01](labs/lab-01-the-adder-you-already-trust-overview.md).
- Read [Your first cocotb test](guide/your-first-cocotb-test.md),
  [Clocks, resets and triggers](guide/clocks-resets-and-triggers.md),
  [cocotb 2.x and older tutorials](guide/cocotb-2x-vs-every-tutorial.md),
  [Driving and checking a design](guide/driving-and-checking.md) and
  [Waveforms](guide/waveforms.md).
- Work in a terminal on the noVNC desktop (Part 5 opens graphical viewers), in the package
  directory:

  ```bash
  mod dd104
  cd labs/cocotb-intro
  ```

The design is `rtl/counter.sv`: an 8-bit counter with an enable, a parallel load that beats the
enable, and an active-low synchronous reset. `tc` is high on the cycle before the count wraps.
`rtl/counter_broken.sv` is the same file with `en &` deleted from `tc`.

## Part 1: Your first test

What does the smallest cocotb test print, and what goes wrong if it reads `q` at the clock edge?

1. Run the minimal test:

   ```bash
   make hello
   ```

   You should see `Running on Icarus Verilog version 14.0 (devel)`, then
   `q = 1 after one enabled clock. That is the whole test.` at `21.00ns`, and
   `TESTS=1 PASS=1 FAIL=0 SKIP=0` with `21.00` ns of simulated time.

2. Try the two commands that look like they should run the test:

   ```bash
   python3 test_01_hello.py; echo "exit=$?"
   python3 -m pytest test_01_hello.py; echo "exit=$?"
   ```

   The first prints nothing and `exit=0`. The second prints `collected 0 items` and
   `no tests ran`, and `exit=5`. Neither started a simulator, so neither ran a test. Only `make`
   does that here.

3. Make the clock-edge race happen. Copy the test and delete its `Timer` line:

   ```bash
   cp test_01_hello.py test_norace.py
   ```

   Open `test_norace.py` and delete the line `await Timer(1, unit="ns")`, the one between the
   last `await RisingEdge(dut.clk)` and the final `assert`. Before you run it, write down what you
   expect the `assert` to read from `q`. Then run it through `sim.mk` directly, with its own build
   directory:

   ```bash
   make -f sim.mk sim TB=test_norace SIM_BUILD=build/norace
   ```

   You should see the test fail at `20.00ns` with
   `after one enabled clock q is 00000000, expected 1`, then `TESTS=1 PASS=0 FAIL=1`. The `make`
   error lines after the table are cocotb's makefile reporting the failed test.

4. Read the failure. Which lines are your assertion message, and which are pytest's assertion
   rewriting (`assert ... + where ...`)? Why does the message print `00000000` and not `0`?

   <details>
   <summary>Answer</summary>

   Your message is the text after `AssertionError:`, and it also appears on the first line. The
   `assert ... + where ...` lines are pytest taking your `assert` apart and showing what each piece
   evaluated to. The message prints `00000000` because `dut.q.value` is a `LogicArray`, which can
   hold `X` and `Z`, so printing it gives the bit pattern. `int(dut.q.value)` would give `0`.
   [Your first cocotb test](guide/your-first-cocotb-test.md#reading-a-value-at-the-clock-edge)
   has the full explanation.

   </details>

Check: `make hello` passes, and `test_norace` fails with `q is 00000000` one clock early.

## Part 2: Triggers

How long does each trigger really wait, and is the counter's reset synchronous?

1. Run the trigger tests:

   ```bash
   make triggers
   ```

   You should see `TESTS=6 PASS=6 FAIL=0 SKIP=0` and `1832.51` ns of simulated time.

2. Find these lines in the log and match each to its section of
   [Clocks, resets and triggers](guide/clocks-resets-and-triggers.md):

   ```
   10 edges counted from t=0 took 90 ns (nine periods -- the edge at t=0 was free)
   q read AT the rising edge : 00000000
   q read 1 ns after the edge: 00000001
   ClockCycles(clk, 5) from 1 ns past an edge: 49 ns
   rst_n low, no clock edge yet: q = 0x5A
   one rising edge later     : q = 0x00
   First(RisingEdge(dut.tc), Timer(200, unit='ns')) -> the Timer won
   ```

3. Why did ten edges counted from t = 0 take 90 ns and not 100?

   <details>
   <summary>Answer</summary>

   `Clock.start()` drives the clock high at t = 0. That first `0`→`1` transition is a rising edge
   and takes no time, so ten edges from t = 0 span nine periods.

   </details>

4. The reset lines answer a question about the design: is the reset synchronous or asynchronous?
   Write down which, and which line tells you.

   <details>
   <summary>Answer</summary>

   Synchronous. `rst_n low, no clock edge yet: q = 0x5A` shows `q` keeping its value with reset
   asserted, and `one rising edge later` shows it cleared on the first edge. If the first line had
   printed `0x00`, the reset would be asynchronous.

   </details>

Check: six tests pass in 1832.51 ns, and you can say why ten edges from t = 0 took 90 ns.

## Part 3: The 1.x traps

Which cocotb 1.x forms still run on cocotb 2.0.1, and which fail?

1. Before you run them, write down which of the four files in `oldapi/` you expect to pass. The
   file names say which 1.x form each one uses. Then run them:

   ```bash
   make oldapi
   ```

   You should see four results in order:

   | File | Result |
   |---|---|
   | `oldapi/test_1x_units.py` | `DeprecationWarning: The 'units' argument has been renamed to 'unit'.`, then `TESTS=1 PASS=1` |
   | `oldapi/test_1x_fork.py` | `AttributeError: module 'cocotb' has no attribute 'fork'`, `TESTS=1 PASS=0 FAIL=1` |
   | `oldapi/test_1x_assign.py` | `TypeError: '<=' not supported between instances of 'LogicObject' and 'int'`, `FAIL=1` |
   | `oldapi/test_1x_imports.py` | `ModuleNotFoundError: No module named 'cocotb.binary'`, and no results table, because it failed while cocotb was importing the file |

2. Which of the four is the most dangerous to find in old code?

   <details>
   <summary>Answer</summary>

   `units=`, the one that passed. Old code that still runs gives no sign that it will break in a
   later release; the deprecation warning is one line that scrolls past.

   </details>

3. Run the suite with a mistyped test filter:

   ```bash
   make nothing
   ```

   You should see `No tests left after filtering with: chekcing$`, no results table, and
   `exit status 0, no FAIL anywhere, and zero tests ran.`

4. Look at what cocotb recorded:

   ```bash
   grep -c "<skipped" build/nothing.xml
   ```

   You should see `6`: six tests, all skipped.

5. Ask the installed cocotb which keywords `@cocotb.test()` takes:

   ```bash
   python3 -c "import cocotb, inspect; print(inspect.signature(cocotb.test))"
   ```

   You should see one long line starting `(obj: Union[Callable[..., Coroutine[...` and listing
   `timeout_time`, `timeout_unit`, `expect_fail`, `expect_error`, `skip`, `stage` and `name`.

Check: you can say which of the four 1.x forms passed, and why `make nothing` exits 0.

## Part 4: A two-sided verdict

Does the checking testbench pass the good counter, fail the broken one, and notice a counter you
break yourself?

1. Run everything:

   ```bash
   make
   ```

   This runs `hello`, `triggers`, `sim` and `broken`: four simulator runs and nineteen tests, 0.3 s
   of simulation. Wall clock is 8–14 s depending on how busy the machine is. You should see:

   ```
   ------------------------------------------------------------------------
    VERDICT
   ------------------------------------------------------------------------
      test_03_checking.py PASSED on rtl/counter.sv
      test_03_checking.py FAILED on rtl/counter_broken.sv
   ```

2. Scroll up to the `make broken` section. One test fails and five pass. Find the failing test's
   message, starting `q is 0xFF and en is 0, so the count is NOT about to wrap, but tc is 1.`
   Which line of RTL does it send you to?

   <details>
   <summary>Answer</summary>

   The `tc` assignment. The message goes on to say that `tc` should be `en & (q == 8'hFF)` and
   that a `tc` of 1 here means the `en &` is missing, which is exactly the difference between
   `rtl/counter.sv` and `rtl/counter_broken.sv`.

   </details>

3. Find the two log lines from `against_a_reference_model`. How many of its 600 random clocks
   had `q = 0xFF` with `en` low?

   <details>
   <summary>Answer</summary>

   None: `of those 600 clocks, 0 had q = 0xFF with en low`. The counter only reaches `0xFF` while
   it is running, and while it is running the broken `tc` and the correct one agree, so the most
   thorough test in the file never reaches the one situation that exposes the bug.

   </details>

4. Break the good counter. Open `rtl/counter.sv` and change

   ```systemverilog
   else if (en)     q <= q + 8'd1;
   ```

   to `q <= q + 8'd2`. Before you run, write down which of the six tests in
   `test_03_checking.py` you expect to fail. Then run:

   ```bash
   make sim
   ```

   You should see three of the six tests fail: `load_then_count`, `the_wrap_is_where_the_bugs_live`
   and `against_a_reference_model`, with `TESTS=6 PASS=3 FAIL=3`. The first failure is on the
   first comparison:

   ```
   31.00ns WARNING  .. load_then_count.load_then_count counting from 0x30: expected 0x31, got 0x32 -- a difference of +1
   ```

   The `assert 50 == 49` line under it is pytest's assertion rewriting showing the same numbers in
   decimal. `the_wrap_is_where_the_bugs_live` shows the whole trajectory,
   `[(255, 1), (1, 0), (3, 0), (5, 0), (7, 0)]`: the counter stepping by two.

5. What do `a difference of +1` and the `q=0x32 ... at t=31 ns` in the full message tell you?

   <details>
   <summary>Answer</summary>

   The `+1` is the diagnosis: one counted edge moved `q` one further than it should have.
   `t=31 ns` says it went wrong on the first counted edge rather than drifting in later.

   </details>

6. Undo the edit and run `make sim` again. You should see `TESTS=6 PASS=6 FAIL=0 SKIP=0`.

Check: `make` prints the verdict above, and `rtl/counter.sv` is back to `q + 8'd1`.

## Part 5: Waveforms

The broken counter's log is identical to the good one's. What does its bug look like in a
waveform?

1. Make a waveform:

   ```bash
   make waves
   ```

   You should see the log lines from `reset released at t = 11 ns` to
   `finished at t = 211 ns with q = 0x05`, including `loaded 0xFF at t = 121 ns  <-- zoom here`,
   then `FST info: dumpfile ... opened for output.` after the results table (normal), and two
   `wrote` lines for `counter.fst` and `counter.vcd`.

2. Open it in Surfer, from this terminal:

   ```bash
   surfer counter.fst
   ```

   Click `counter` in the Scopes pane, then add `clk`, `rst_n`, `en`, `load`, `q` and `tc` from the
   Variables pane. Zoom to 121 ns. Remember the ruler is in picoseconds, so look near `121000 ps`.

   You should see `q` reach `ff` at 121 ns, hold for three clocks with `en` low, and `tc` go high
   for exactly one clock before `q` wraps to `00`.

3. Save yourself the clicking next time with a command file:

   ```bash
   printf 'module_add counter\n' > view.sf
   surfer -c view.sf counter.fst
   ```

   You should see every signal in `counter` added at once.

4. Open the same file in GTKWave, with the shipped save file:

   ```bash
   gtkwave counter.fst counter.gtkw
   ```

   If the wave pane looks empty, you are looking at the first few picoseconds. Use
   `View → Zoom → Zoom Best Fit` (`Ctrl` `Alt` `F`). You should then see the same 211 ns run.

5. Make a waveform of the broken counter. Before you open it, sketch what you expect `tc` to do
   from 121 ns, while `q` sits at `0xFF` with `en` low.

   ```bash
   make -f sim.mk sim TB=test_04_waves WAVES=1 RTL=rtl/counter_broken.sv \
        SIM_BUILD=build/bw COCOTB_RESULTS_FILE=build/bw.xml
   surfer build/bw/counter.fst
   ```

   The test passes, and its log is identical line for line to the good run's. Add the same six
   signals.

   You should see `tc` go high at 121 ns, when `q` becomes `0xFF`, and stay high for four clocks,
   including the three where `en` is low and the counter is not moving. On the good counter it was
   one clock wide.

Check: you have seen `tc` one clock wide on the good counter and four clocks wide on the broken
one.

## Expected results

| Check | Expected | |
|---|---|---|
| `make hello` | `TESTS=1 PASS=1`, `21.00` ns | exact |
| `make triggers` | `TESTS=6 PASS=6`, `1832.51` ns | exact |
| `make nothing` | no results table, exit 0, six `<skipped` in `build/nothing.xml` | exact |
| `make`, verdict | `PASSED on rtl/counter.sv`, `FAILED on rtl/counter_broken.sv` | exact |
| `make` wall clock | 8–14 s | ballpark |
| `make sim` with `q + 8'd2` | `TESTS=6 PASS=3 FAIL=3` | exact |
| `make waves`, VCD size | `1098` bytes | exact |

## Finishing

You're done when your `test_norace` fails one clock early, your `q + 8'd2` counter fails 3 of 6
tests, and `make` on the restored `rtl/counter.sv` prints both halves of the verdict.

Submit: nothing for this lab. `make clean` removes `build/`, the waveform files and the caches; it
does not remove `test_norace.py`, `view.sf` or a `test_mine.py` from Going further, so delete those
yourself if you want a clean package.

## Going further (optional)

To write your own variant of the checking tests, copy the file and run it through `sim.mk`, giving
each run its own build directory:

```bash
cp test_03_checking.py test_mine.py
make -f sim.mk sim TB=test_mine SIM_BUILD=build/mine
make -f sim.mk sim TB=test_mine RTL=rtl/counter_broken.sv SIM_BUILD=build/mine-broken
```

You should see `TESTS=6 PASS=6` on the first and `TESTS=6 PASS=5 FAIL=1` on the second. The second
run failing is the half that shows your testbench can see the bug. (`make sim TB=...` does not
work here: the package's `sim` target always runs `test_03_checking`.)

Next on the Course path: read [Two simulators](guide/two-simulators-two-jobs.md) and
[SimProc in one page](guide/simproc-in-one-page.md), then do
[Lab 02: The only test this chip has](labs/lab-02-the-only-test-this-chip-has-overview.md).
