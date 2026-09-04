"""
DD104 — reading a cocotb results file, and the one distinction every verdict
in this course depends on.

    from verdict import Result, read_results

────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
────────────────────────────────────────────────────────────────────────────
A test that does not pass has not necessarily *checked* anything.  There are
two completely different ways for a test to come back not-green:

    the check fired          you drove the design, you compared what came out
                             against what should have come out, and they did
                             not match.  This is the good one.  It is a
                             statement about the DESIGN.

    the test blew up         `NameError`, `TypeError`, `AttributeError`, an
                             import that failed, a variable you never spelled
                             the same way twice.  Python raised before the
                             comparison happened, or instead of it.  This is a
                             statement about the TESTBENCH, and it says
                             nothing whatever about the design.

Both land in `results.xml` as `<failure>`.  cocotb 2.0.1 never writes an
`<error>` element at all -- MEASURED, see the note at the bottom of this file
-- so a checker that looks for one and treats every `<failure>` alike will
count a testbench that crashed as a testbench that caught a bug.

DD104 shipped exactly that bug, and a student was told

    3 of 3 ALU bugs caught.
    Every bug the catalogue puts inside the ALU.

by a testbench whose exhaustive test raised
`NameError: name 'value_per_op' is not defined` on every core it was pointed
at.  The three "catches" were three crashes.  A verification course that
issues a false PASS has failed at the only thing it teaches, so the
distinction lives here, in one file, and every verdict in DD104 reads it from
this module rather than re-deriving it.

────────────────────────────────────────────────────────────────────────────
HOW THE TWO ARE TOLD APART
────────────────────────────────────────────────────────────────────────────
cocotb writes the exception's class name into `error_type=`.  `CHECK_FIRED`
below is the list of class names that mean "a check in this course fired".
Everything else is a testbench that blew up.

A whitelist, and not a blacklist, on purpose: a blacklist is wrong the first
time somebody's testbench raises an exception nobody thought of, and being
wrong in that direction means printing PASS.  Being wrong in the other
direction prints FAIL and a sentence naming the exception, which a student can
read and act on.  When you add a new way for this course's harness to say "the
design misbehaved", add it here too.
"""

import xml.etree.ElementTree as ET


# ── the four ways a DD104 check says "the design is wrong" ──────────────────
CHECK_FIRED = {

    # `assert got == want, ...`, and `raise AssertionError(...)`.  This is
    # what almost every test in this course raises.
    "AssertionError",

    # cocotb's `with_timeout(...)` expired: the edge you were waiting for
    # never came.  A design that never raises `done` fails exactly here.
    "SimTimeoutError",

    # simproc.py raises this when the core never reaches its parking loop
    # (`run()`), or when the chip never answers a command (`recv_byte()`).
    # B13 and B12 are caught this way and no assert is involved.
    "TimeoutError",

    # simproc.py raises this when the chip drove X onto the TX pin -- the
    # reply is not eight 0s and 1s.  It is how B12 is caught at
    # clk_per_bit = 16, which is a documented, expected result in Lab 06.
    "ValueError",
}


def classify(error_type):
    """'failed' if a check fired, 'errored' if the testbench blew up.

    A `<failure>` with no `error_type` at all is cocotb's
    "Test initialization failed" -- the test never started, so no check in it
    can have fired."""
    if not error_type:
        return "errored"
    return "failed" if error_type in CHECK_FIRED else "errored"


class Outcome:
    """What happened to one `@cocotb.test()`.

    kind is 'passed', 'failed' (a check fired), 'errored' (the test blew up)
    or 'skipped' (it never ran)."""

    def __init__(self, name, kind, error_type="", message="", sim_time_ns=0.0):
        self.name = name
        self.kind = kind
        self.error_type = error_type
        self.message = message
        self.sim_time_ns = sim_time_ns

    @property
    def one_line(self):
        first = self.message.splitlines()[0] if self.message else "(no message)"
        return f"{self.error_type or 'failure'}: {first}"


class Result:
    """What one simulation run did, with erroring tests kept separate from
    failing ones.

    `failures` is assertion failures ONLY.  If you are asking "did my
    testbench catch the bug?", `failures` -- or better, `.caught` -- is the
    list to ask.  `errors` is tests that blew up, and a run with any of those
    in it cannot produce a verdict at all."""

    def __init__(self, outcomes, seconds, log, launched):
        self.outcomes = outcomes
        self.seconds = seconds
        self.log = log
        self.launched = launched

    # ── the four buckets ────────────────────────────────────────────────────
    def _of(self, kind):
        return [o for o in self.outcomes if o.kind == kind]

    @property
    def tests(self):
        return len(self.outcomes)

    @property
    def passes(self):
        return self._of("passed")

    @property
    def failures(self):
        """(name, 'Type: message') for tests whose CHECK FIRED."""
        return [(o.name, o.one_line) for o in self._of("failed")]

    @property
    def errors(self):
        """(name, 'Type: message') for tests that BLEW UP."""
        return [(o.name, o.one_line) for o in self._of("errored")]

    @property
    def skipped(self):
        return [o.name for o in self._of("skipped")]

    @property
    def ran(self):
        """Tests that actually executed. A skipped test is not a passing test."""
        return self.tests - len(self.skipped)

    @property
    def sim_time_ns(self):
        """Total simulated nanoseconds across every test in the run."""
        return sum(o.sim_time_ns for o in self.outcomes)

    # ── the three questions a verdict asks ──────────────────────────────────
    @property
    def broken(self):
        """True if any test blew up. Such a run answers no question at all."""
        return self.launched and bool(self.errors)

    @property
    def all_passed(self):
        """Every test ran, and every test passed."""
        return (self.launched and self.ran > 0
                and not self.failures and not self.errors)

    @property
    def caught(self):
        """At least one check fired, and nothing blew up."""
        return (self.launched and self.ran > 0
                and bool(self.failures) and not self.errors)

    def summary(self):
        if not self.launched:
            return "the simulator did not run"
        if self.tests == 0:
            return "0 tests ran"
        n = f"{self.tests} test" + ("" if self.tests == 1 else "s")
        if self.ran == 0:
            return f"{n}, none ran ({len(self.skipped)} skipped)"
        bits = []
        if self.errors:
            bits.append(f"{len(self.errors)} BLEW UP")
        if self.failures:
            bits.append(f"{len(self.failures)} FAILED")
        if self.skipped:
            bits.append(f"{len(self.skipped)} skipped")
        if not bits:
            return f"{n}, all passed"
        return f"{n}, " + ", ".join(bits)

    def mark(self, expectation):
        """The word in the left-hand column of a report row.

        expectation is 'pass' (this core is good, the tests must all pass) or
        'fail' (this core is broken, a check must fire)."""
        if self.broken:
            return "BROKEN"
        if expectation == "pass":
            return "ok" if self.all_passed else "FAIL"
        return "caught" if self.caught else "MISSED"


# ── reading the file ────────────────────────────────────────────────────────

def read_results(path, seconds=0.0, log="", launched=True):
    """Parse a cocotb results.xml into a Result."""
    outcomes = []
    for case in ET.parse(path).getroot().iter("testcase"):
        name = case.get("name") or "(unnamed)"
        try:
            sim_ns = float(case.get("sim_time_ns") or 0.0)
        except ValueError:
            sim_ns = 0.0

        if case.find("skipped") is not None:
            outcomes.append(Outcome(name, "skipped", sim_time_ns=sim_ns))
            continue

        # cocotb 2.0.1 writes only <failure>; older JUnit writers also emit
        # <error>. Read either, so this works on both.
        bad = list(case.findall("failure")) + list(case.findall("error"))
        if not bad:
            outcomes.append(Outcome(name, "passed", sim_time_ns=sim_ns))
            continue

        e = bad[0]
        etype = (e.get("error_type") or e.get("type") or "").strip()
        text = (e.get("error_msg") or e.get("message") or e.get("msg")
                or e.text or "").strip()
        outcomes.append(Outcome(name, classify(etype), etype, text, sim_ns))
    return Result(outcomes, seconds, log, launched)


def not_launched(seconds=0.0, log=""):
    return Result([], seconds, log, launched=False)


# ── the words the verdict says ──────────────────────────────────────────────

def report_problems(result, indent="        ", limit=6):
    """Print the tests that blew up, then the ones whose check fired.

    Blown-up tests first and labelled, because they are the ones that have to
    be dealt with before any of the rest of the run means anything."""
    for name, msg in result.errors[:limit]:
        print(f"{indent}{name}   <- this test BLEW UP; it checked nothing")
        print(f"{indent}    {msg[:90]}")
    for name, msg in result.failures[:limit]:
        print(f"{indent}{name}")
        print(f"{indent}    {msg[:90]}")
    if result.skipped:
        print(f"{indent}skipped, so never run: {', '.join(result.skipped[:6])}")


def broken_testbench_verdict(result, where):
    """The FAIL text for a run in which a test blew up. `where` names the core
    it was pointed at, e.g. 'the golden core' or 'B01_sub_operands_swapped'."""
    n = len(result.errors)
    types = sorted({t.split(":")[0] for _, t in result.errors})
    print(f" VERDICT: FAIL -- {n} of your tests did not run to the end.")
    print(f"   On {where}, {'it raised' if n == 1 else 'they raised'} "
          f"{', '.join(types)} before any comparison happened.")
    print("")
    print("   That is not a caught bug and it is not a passing test. It is")
    print("   Python failing inside your testbench. An exception that is not")
    print("   an AssertionError did not compare anything, so it cannot tell")
    print("   you whether the design is right or wrong -- on this core or on")
    print("   any other.")
    print("")
    print("   Fix the testbench first, then ask for a verdict. `make sim` on")
    print("   its own prints the whole traceback.")


def no_tests_ran_verdict(result):
    """The FAIL text for a run where every test was skipped or none existed."""
    if result.tests == 0:
        print(" VERDICT: FAIL -- the run produced zero tests.")
        print("   cocotb found no @cocotb.test() to run. Check that TB= names")
        print("   the module (test_mine), not the file (test_mine.py).")
    else:
        print(f" VERDICT: FAIL -- all {result.tests} tests were skipped.")
        print("   Nothing ran, so nothing was checked. A COCOTB_TESTCASE with a")
        print("   typo in it does this: cocotb filters every test out, writes")
        print("   <skipped/> for all of them, and exits 0.")


# ────────────────────────────────────────────────────────────────────────────
# MEASURED, cocotb 2.0.1, workbench hpretl/iic-osic-tools:2026.08
# ────────────────────────────────────────────────────────────────────────────
# cocotb/regression.py writes results.xml through cocotb/_xunit_reporter.py.
# The only three things it can put inside a <testcase> are:
#
#   nothing                                     the test passed
#   <skipped/>                                  skipped, or filtered out
#   <failure error_type="X" error_msg="..."/>   the test raised X
#
# with one special case: a test that could not be initialised gets
# <failure msg="Test initialization failed"/> and NO error_type.
#
# It never writes <error>.  `error_type` is `type(result).__name__`, so it is
# the bare class name: AssertionError, NameError, TimeoutError, SimTimeoutError.
# An observed example, from a testbench with an undefined variable in its
# failure path, run against a deliberately broken ALU:
#
#   <testcase name="t02_every_vector_the_alu_can_be_given" ...>
#     <failure error_type="NameError" error_msg="name 'value_per_op' is not defined" />
#   </testcase>
#
# `sim_time_ns` is on the <testcase> element and is the simulated time that
# test consumed. Lab 01 uses it to count vectors: one vector is 1 ns there.
