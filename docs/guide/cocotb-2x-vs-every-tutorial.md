# ⚠ cocotb 2.x vs every tutorial you will find

**Question this page answers:** *I copied a cocotb example off the internet and it does not
work / it works but prints warnings. Which of us is wrong?*

Neither. The example is right, for cocotb **1.x**. This course runs cocotb **2.0.1**, and 2.0
renamed and removed a lot.

The workbench has cocotb 2.0.1 and you can prove it in one line, before you trust anything else
on this page:

```bash
cocotb-config --version
```

```
2.0.1
```

Almost every cocotb tutorial, blog post, StackOverflow answer, ChatGPT completion and university
lab handout in existence was written against 1.x. You will find them. Some will run. **The ones
that run are the dangerous ones**, and this page is ordered accordingly.

Everything below was run in the workbench and the outputs are pasted verbatim. The four
demonstration files are complete and shipped:

```bash
cd labs/cocotb-intro
make oldapi
```

---

## Tier 1 — the ones that still work

### `units=` instead of `unit=`

**This is the single most common 1.x form, and cocotb 2.0.1 accepts it.**

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

**It passes.** The warning is one `WARNING` line among the INFO lines, it scrolls past, and
nothing about your run says "you are writing code that will stop working."

Write `unit=`. The old spelling is a deprecation, and a deprecation is a countdown.

### `.integer`, `.binstr`, `.signed_integer`, `.buff`

Same story — they work, they warn, and each names its replacement:

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

`sig.value.is_resolvable` is **not** deprecated and is the right way to ask "does this have any
`X` in it?" before converting.

### `MODULE` and `TOPLEVEL` in the Makefile

1.x makefiles say:

```make
TOPLEVEL = counter
MODULE   = test_tiny
```

Under 2.0.1's `Makefile.sim` these still work, and warn once:

```
/usr/local/lib/python3.12/dist-packages/cocotb_tools/makefiles/simulators/Makefile.icarus:66: Using MODULE is deprecated, please use COCOTB_TEST_MODULES instead.
...
** TESTS=1 PASS=1 FAIL=0 SKIP=0                  1.00           0.00       1178.18  **
```

The 2.x names are `COCOTB_TOPLEVEL` and `COCOTB_TEST_MODULES`. Use those; DD104's `sim.mk` does.

> The mapping lives in cocotb's *makefiles*, not in cocotb itself. If you ever drive a
> simulation without them — the Python runner, `pytest`, a hand-written `vvp` command line —
> only `COCOTB_TEST_MODULES` is read, and `MODULE` is silently ignored.

### `COCOTB_TESTCASE`

Deprecated in favour of `COCOTB_TEST_FILTER`, which takes a regular expression:

```
     0.00ns WARNING  py.warnings   DeprecationWarning: COCOTB_TESTCASE is deprecated in favor of COCOTB_TEST_FILTER
```

Read the next section before you use either.

---

## Tier 2 — the ones that fail loudly

Good news: these produce a traceback with a line number, and you will fix them in seconds once
you have seen each one once.

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

`cocotb.start_soon(...)` is the replacement and takes the same argument. (`cocotb.start(...)`
also exists — it is the `await`able version that lets the new task run before you continue.)

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

A `TypeError` about `<=` reads like a comparison bug, because Python thinks it *is* one. It is
not. It is an assignment that was removed.

### `cocotb.binary` and `cocotb.result`

```python
from cocotb.binary import BinaryValue
from cocotb.result import TestFailure
```

These fail **while cocotb is importing your file**, before any test runs — so there is no test
name in the output and no results table at all:

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

`cocotb.result` is subtler. **The module still exists** — it is now empty — so the error is
about a *name*, which reads like a typo:

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

### Scary output that is not your fault

When cocotb fails during discovery — a missing module, an import error, no tests found — it
prints a **second** traceback after the real one:

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

**Ignore all of it.** That is cocotb's error handler falling over while reporting your error,
because there was no running test to abort. The real problem is the traceback *above* it.
`RegressionManager`, `_running_test`, `gpi` and `_sim_event` are not names from your code, and
that is how you tell.

---

## Tier 3 — the one that is worse than a failure

None of the above loses you a day. This does.

```bash
make nothing
```

runs the real six-test suite with one letter transposed in the test name:

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

Look at what is *missing*: there is **no results table**. No `TESTS=`, no `PASS=`, no `FAIL=`.
The whole run is three INFO lines, one WARNING, and a clean exit. In CI that is a green tick.

`results.xml` records the truth, if anyone reads it:

```xml
<testcase name="load_then_count" classname="test_03_checking" ... >
  <skipped />
</testcase>
```

Six tests. Six `<skipped/>`. Zero run.

**Reflex check, and this is the one to actually adopt: after every cocotb run, read the
`TESTS=` line and confirm the count is the number of tests you wrote.** Not the colour, not the
exit code — the count. A cocotb run that tested nothing looks exactly like a cocotb run that
tested everything, except for a line that is not there.

This is DD104's whole argument in miniature. SimProc shipped with one test that passes on
thirteen deliberately broken processors; a filter typo passes on all of them and on the good one
too. "My tests pass" is not a result. "Six tests ran, five passed on the good core, and this
one fails on the broken core" is a result.

---

## The conversion table

| you found (1.x) | write this (2.0.1) | what happens if you don't |
|---|---|---|
| `Timer(1, units="ns")` | `Timer(1, unit="ns")` | works, `DeprecationWarning` |
| `Clock(clk, 10, units="ns")` | `Clock(clk, 10, unit="ns")` | works, `DeprecationWarning` |
| `Clock(clk, 10)` | `Clock(clk, 10, unit="ns")` | works — as a **10 ps** clock |
| `cocotb.fork(coro)` | `cocotb.start_soon(coro)` | `AttributeError: module 'cocotb' has no attribute 'fork'` |
| `dut.sig <= 1` | `dut.sig.value = 1` | `TypeError: '<=' not supported between instances of 'LogicObject' and 'int'` |
| `dut.sig = 1` | `dut.sig.value = 1` | `AttributeError: ... Did you forget to add \`.value\`?` (silent in 1.x) |
| `sig.value.integer` | `int(sig.value)` | works, `DeprecationWarning` |
| `sig.value.binstr` | `str(sig.value)` | works, `DeprecationWarning` |
| `sig.setimmediatevalue(v)` | `sig.value = Immediate(v)`, from `cocotb.handle` | works, `DeprecationWarning` |
| `from cocotb.binary import BinaryValue` | `from cocotb.types import LogicArray` | `ModuleNotFoundError` at import |
| `raise TestFailure("x")` | `assert cond, "x"` | `AttributeError` on `cocotb.result` |
| `@cocotb.coroutine` / `yield` | `async def` / `await` | `AttributeError: module 'cocotb' has no attribute 'coroutine'` |
| `from cocotb.triggers import Join` | `from cocotb.task import Join` | works, `DeprecationWarning` |
| `MODULE=` | `COCOTB_TEST_MODULES=` | works in makefiles, warns; ignored elsewhere |
| `TOPLEVEL=` | `COCOTB_TOPLEVEL=` | works, warns |
| `TESTCASE=` / `COCOTB_TESTCASE=` | `COCOTB_TEST_FILTER=` (a regex) | works, warns |

## When you are stuck, read the shipped docs, not the web

The installed version's own documentation is the only reference guaranteed to match:

```bash
python3 -c "import cocotb, inspect; print(inspect.signature(cocotb.test))"
```

```
(obj: Union[Callable[..., Coroutine[cocotb._base_triggers.Trigger, NoneType, NoneType]],
 cocotb._decorators.Parameterized, NoneType] = None, *, timeout_time: Optional[float] = None,
 timeout_unit: Literal['step', 'fs', 'ps', 'ns', 'us', 'ms', 'sec'] = 'step',
 expect_fail: bool = False, expect_error: Union[Type[BaseException], Tuple[Type[BaseException],
 ...]] = (), skip: bool = False, stage: int = 0, name: Optional[str] = None) -> ...
```

(wrapped here to fit; it comes out as one long line)

`inspect.signature` on the thing you are actually running beats any tutorial, and it takes five
seconds. If a keyword you read about is not in that list, it is 1.x.

Next: [Driving and checking a design](guide/driving-and-checking.md).
