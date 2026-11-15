# cocotb 2.x and older tutorials

This page answers: *I copied a cocotb example off the internet and it does not work, or it works
but prints warnings. Which of us is wrong?*

Neither. The example is right for cocotb 1.x. This course runs cocotb 2.0.1, and 2.0 renamed
and removed a lot.

Almost every cocotb tutorial, blog post, Stack Overflow answer, chatbot completion and university
lab handout was written against 1.x. Some of them still run on 2.0.1, and those are the dangerous
ones, so this page starts with them.

Everything below was run in the workbench and the output is pasted unedited. The four
demonstration files ship in
[`labs/cocotb-intro/oldapi/`](https://github.com/uoftasic/dd104/tree/main/labs/cocotb-intro/oldapi),
and you'll run them in [cocotb on a counter, Part 3](../labs/cocotb-intro-overview.md#part-3-the-1x-traps).

## Forms that still work

### `units=` instead of `unit=`

This is the most common 1.x form, and cocotb 2.0.1 accepts it.

```python
cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
await Timer(20, units="ns")
```

```
     0.00ns WARNING  py.warnings   /work/labs/cocotb-intro/oldapi/test_1x_units.py:24: DeprecationWarning: The 'units' argument has been renamed to 'unit'.
                                     cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
...
    41.00ns INFO     cocotb.regression   test_1x_units.the_old_spelling_still_runs passed
** TESTS=1 PASS=1 FAIL=0 SKIP=0                              41.00           0.00      19633.12  **
```

It passes. The warning is one `WARNING` line among the INFO lines, it scrolls past, and nothing
in the run tells you this code will stop working. Write `unit=`. A deprecation means the old
spelling will be removed in a later release.

### `.integer`, `.binstr`, `.signed_integer`, `.buff`

Same story: they work, they warn, and each warning names its replacement.

```
    41.00ns WARNING  py.warnings   DeprecationWarning: `logic_array.integer` getter is deprecated. Use `logic_array.to_unsigned()` instead.
    41.00ns INFO     cocotb.counter   v.integer = 42
    41.00ns WARNING  py.warnings   DeprecationWarning: `logic_array.binstr` getter is deprecated. Use `str(logic_array)` instead.
    41.00ns INFO     cocotb.counter   v.binstr  = 00101010
```

| 1.x | 2.x |
|---|---|
| `sig.value.integer` | `int(sig.value)` or `sig.value.to_unsigned()` |
| `sig.value.binstr` | `str(sig.value)` |
| `sig.value.signed_integer` | `sig.value.to_signed()` |
| `sig.value.buff` | `sig.value.to_bytes(byteorder="big")` |

`sig.value.is_resolvable` is not deprecated. It is the right way to ask whether a value contains
any `X` before you convert it.

### `MODULE` and `TOPLEVEL` in the Makefile

1.x makefiles say:

```make
TOPLEVEL = counter
MODULE   = test_tiny
```

Under 2.0.1's `Makefile.sim` these still work and warn once:

```
/usr/local/lib/python3.12/dist-packages/cocotb_tools/makefiles/simulators/Makefile.icarus:66: Using MODULE is deprecated, please use COCOTB_TEST_MODULES instead.
...
** TESTS=1 PASS=1 FAIL=0 SKIP=0                  1.00           0.00       1178.18  **
```

The 2.x names are `COCOTB_TOPLEVEL` and `COCOTB_TEST_MODULES`. Use those; DD104's `sim.mk` does.

> The mapping from old names to new lives in cocotb's makefiles, not in cocotb itself. If you
> drive a simulation without them (the Python runner, `pytest`, a hand-written `vvp` command
> line), only `COCOTB_TEST_MODULES` is read and `MODULE` is silently ignored.

### `COCOTB_TESTCASE`

Deprecated in favour of `COCOTB_TEST_FILTER`, which takes a regular expression:

```
     0.00ns WARNING  py.warnings   DeprecationWarning: COCOTB_TESTCASE is deprecated in favor of COCOTB_TEST_FILTER
```

Read [A filter that runs nothing](#a-filter-that-runs-nothing) before you use either.

## Forms that fail loudly

These produce a traceback with a line number. Once you have seen each one, you will fix it in
seconds.

### `cocotb.fork` → `cocotb.start_soon`

```python
cocotb.fork(Clock(dut.clk, 10, unit="ns").start())
```

```
     0.00ns WARNING  ..b.Test fork_is_gone.fork_is_gone   module 'cocotb' has no attribute 'fork'
                                                        Traceback (most recent call last):
                                                          File "/work/labs/cocotb-intro/oldapi/test_1x_fork.py", line 22, in fork_is_gone
                                                            cocotb.fork(Clock(dut.clk, 10, unit="ns").start())   # AttributeError
                                                            ^^^^^^^^^^^
                                                        AttributeError: module 'cocotb' has no attribute 'fork'
```

The replacement is `cocotb.start_soon(...)`, with the same argument. (`cocotb.start(...)` also
exists: it is the `await`able version that lets the new task run before you continue.)

### `dut.sig <= value` → `dut.sig.value = value`

1.x let you assign with `<=`, mimicking Verilog:

```python
dut.rst_n <= 1
```

```
     0.00ns WARNING  ..re.le_is_not_assignment_any_more   '<=' not supported between instances of 'LogicObject' and 'int'
                                                        Traceback (most recent call last):
                                                          File "/work/labs/cocotb-intro/oldapi/test_1x_assign.py", line 25, in le_is_not_assignment_any_more
                                                            dut.rst_n <= 1          # TypeError
                                                            ^^^^^^^^^^^^^^
                                                        TypeError: '<=' not supported between instances of 'LogicObject' and 'int'
```

A `TypeError` about `<=` reads like a comparison bug, because to Python the line is a comparison.
It is an assignment form that was removed.

### `cocotb.binary` and `cocotb.result`

```python
from cocotb.binary import BinaryValue
from cocotb.result import TestFailure
```

These fail while cocotb is importing your file, before any test runs, so there is no test name in
the output and no results table:

```
  (this one never reached 'Running tests' -- it failed while cocotb was
   still importing the file, so no test ran at all)
Traceback (most recent call last):
  ...
  File "/work/labs/cocotb-intro/oldapi/test_1x_imports.py", line 20, in <module>
    from cocotb.binary import BinaryValue     # ModuleNotFoundError, at IMPORT time
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'cocotb.binary'
```

`cocotb.result` is subtler. The module still exists but is now empty, so the error is about a
name, which reads like a typo:

```
AttributeError: module 'cocotb.result' has no attribute 'TestFailure'
```

| 1.x | 2.x |
|---|---|
| `from cocotb.binary import BinaryValue` | `from cocotb.types import LogicArray` |
| `raise TestFailure("...")` | `assert cond, "..."` |
| `raise TestSuccess()` | `cocotb.pass_test()`, or just `return` |
| `@cocotb.coroutine` + `yield` | `async def` + `await` |
| `cocotb.regression.TestFactory` | `@cocotb.parametrize(...)` (`TestFactory` still exists) |

### The second traceback

When cocotb fails during discovery (a missing module, an import error, no tests found), it prints
a second traceback after the real one:

```
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/dist-packages/cocotb/_init.py", line 117, in _sim_event
    cocotb._regression_manager._fail_simulation(msg)
  File "/usr/local/lib/python3.12/dist-packages/cocotb/regression.py", line 899, in _fail_simulation
    self._running_test.abort(self._sim_failure)
    ^^^^^^^^^^^^^^^^^^
AttributeError: 'RegressionManager' object has no attribute '_running_test'
     0.00ns ERROR    gpi   Passing event to upper layer failed
```

Ignore it. That is cocotb's error handler falling over while reporting your error, because there
was no running test to abort. The real problem is the traceback above it. `RegressionManager`,
`_running_test`, `gpi` and `_sim_event` are not names from your code, which is how you can tell.

## A filter that runs nothing

None of the forms above will cost you a day. This one can.

`make nothing` in `labs/cocotb-intro` runs the real six-test suite with one letter transposed in
the test filter:

```make
COCOTB_TESTCASE = chekcing
```

```
     0.00ns INFO     cocotb   Initialized cocotb v2.0.1 from /usr/local/lib/python3.12/dist-packages/cocotb
     0.00ns WARNING  py.warnings   DeprecationWarning: COCOTB_TESTCASE is deprecated in favor of COCOTB_TEST_FILTER
     0.00ns INFO     cocotb   Running tests
     0.00ns WARNING  cocotb.regression   No tests left after filtering with: chekcing$

   exit status 0, no FAIL anywhere, and zero tests ran.
```

Look at what is missing: there is no results table, no `TESTS=`, no `PASS=`, no `FAIL=`. The whole
run is three INFO lines, one WARNING and a clean exit. In CI that is a green tick.

`results.xml` records what happened, if anyone reads it:

```xml
<testcase name="load_then_count" classname="test_03_checking" ... >
  <skipped />
</testcase>
```

Six tests, six `<skipped/>`, none run.

This is the habit to adopt from this page: after every cocotb run, read the `TESTS=` line and
check that the count is the number of tests you wrote. Not the colour, not the exit code, the
count. A cocotb run that tested nothing looks like one that tested everything, except for a line
that is missing.

It is DD104's argument in miniature. SimProc shipped with one test that passes on thirteen broken
processors; a filter typo passes on all of them and on the good one too. "My tests pass" is not a
result. "Six tests ran, they passed on the good core, and this one fails on the broken core" is.

## Conversion table

| You found (1.x) | Write this (2.0.1) | What happens if you don't |
|---|---|---|
| `Timer(1, units="ns")` | `Timer(1, unit="ns")` | Works, `DeprecationWarning` |
| `Clock(clk, 10, units="ns")` | `Clock(clk, 10, unit="ns")` | Works, `DeprecationWarning` |
| `Clock(clk, 10)` | `Clock(clk, 10, unit="ns")` | Works, as a 10 ps clock |
| `cocotb.fork(coro)` | `cocotb.start_soon(coro)` | `AttributeError: module 'cocotb' has no attribute 'fork'` |
| `dut.sig <= 1` | `dut.sig.value = 1` | `TypeError: '<=' not supported between instances of 'LogicObject' and 'int'` |
| `dut.sig = 1` | `dut.sig.value = 1` | `AttributeError: ... Did you forget to add \`.value\`?` (silent in 1.x) |
| `sig.value.integer` | `int(sig.value)` | Works, `DeprecationWarning` |
| `sig.value.binstr` | `str(sig.value)` | Works, `DeprecationWarning` |
| `sig.setimmediatevalue(v)` | `sig.value = Immediate(v)`, from `cocotb.handle` | Works, `DeprecationWarning` |
| `from cocotb.binary import BinaryValue` | `from cocotb.types import LogicArray` | `ModuleNotFoundError` at import |
| `raise TestFailure("x")` | `assert cond, "x"` | `AttributeError` on `cocotb.result` |
| `@cocotb.coroutine` / `yield` | `async def` / `await` | `AttributeError: module 'cocotb' has no attribute 'coroutine'` |
| `from cocotb.triggers import Join` | `from cocotb.task import Join` | Works, `DeprecationWarning` |
| `MODULE=` | `COCOTB_TEST_MODULES=` | Works in makefiles and warns; ignored elsewhere |
| `TOPLEVEL=` | `COCOTB_TOPLEVEL=` | Works, warns |
| `TESTCASE=` / `COCOTB_TESTCASE=` | `COCOTB_TEST_FILTER=` (a regex) | Works, warns |

## Ask the installed cocotb

The installed version's own signatures are the only reference guaranteed to match what you are
running. `inspect.signature(cocotb.test)` prints the keywords the decorator accepts:

```
(obj: Union[Callable[..., Coroutine[cocotb._base_triggers.Trigger, NoneType, NoneType]],
 cocotb._decorators.Parameterized, NoneType] = None, *, timeout_time: Optional[float] = None,
 timeout_unit: Literal['step', 'fs', 'ps', 'ns', 'us', 'ms', 'sec'] = 'step',
 expect_fail: bool = False, expect_error: Union[Type[BaseException], Tuple[Type[BaseException],
 ...]] = (), skip: bool = False, stage: int = 0, name: Optional[str] = None) -> ...
```

(Wrapped here to fit; it comes out as one long line.) If a keyword you read about is not in that
list, it is from 1.x. You'll run this in the lab.

## Check yourself

1. A tutorial's test runs, passes and prints `DeprecationWarning: The 'units' argument has been
   renamed to 'unit'.` Is anything wrong with your result?
2. A run prints no results table and exits 0. What happened?
3. `TypeError: '<=' not supported between instances of 'LogicObject' and 'int'`. What did the
   author of that line mean to write?

Next: [Driving and checking a design](../guide/driving-and-checking.md).
