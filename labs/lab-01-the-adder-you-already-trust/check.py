"""
DD104 Lab 01 — the verdict.

    make check                your testbench against the good adder AND a broken one

A testbench that passes proves nothing on its own.  This one passes:

    @cocotb.test()
    async def it_works(dut):
        pass

It passes on a correct adder, on an adder that drops its carry-in, and on an
adder made of a wire.  It passes on everything, so it distinguishes nothing,
so it is worth nothing.

The result is therefore two-sided, and this script measures both halves:

    it must PASS on src/       -- or you are testing the wrong thing
    it must FAIL on broken/    -- or you are not testing anything

Every DD104 lab from here on uses the same verdict, against a processor
instead of an adder.  This is the small version of it.
"""

import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.abspath(os.path.join(HERE, "..", "common"))
RULE = "=" * 72
THIN = "-" * 72


class Result:
    def __init__(self, tests, failures, seconds, log, launched):
        self.tests = tests
        self.failures = failures
        self.seconds = seconds
        self.log = log
        self.launched = launched

    @property
    def all_passed(self):
        return self.launched and self.tests > 0 and not self.failures

    def summary(self):
        if not self.launched:
            return "the simulator did not run"
        if self.tests == 0:
            return "0 tests ran"
        if not self.failures:
            return f"{self.tests} tests, all passed"
        return f"{self.tests} tests, {len(self.failures)} FAILED"


def run_sim(tb, rtl_dir, build_dir):
    """One cocotb run, launched through the same sim.mk every DD104 lab uses."""
    results = os.path.join(build_dir, "results.xml")
    os.makedirs(build_dir, exist_ok=True)
    if os.path.exists(results):
        os.remove(results)

    cmd = [
        "make", "-f", os.path.join(COMMON, "sim.mk"), "sim",
        f"COMMON={COMMON}", f"TB={tb}", "SIM=icarus", "TOPLEVEL=ripple4",
        f"VERILOG_SOURCES={rtl_dir}/ripple4.sv {rtl_dir}/fulladder.sv",
        f"SIM_BUILD={os.path.join(build_dir, 'sim')}",
        f"COCOTB_RESULTS_FILE={results}",
    ]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    elapsed = time.time() - t0
    log = proc.stdout + proc.stderr

    if not os.path.exists(results):
        return Result(0, [], elapsed, log, launched=False)

    tests, failures = 0, []
    for case in ET.parse(results).getroot().iter("testcase"):
        tests += 1
        bad = list(case.findall("failure")) + list(case.findall("error"))
        if bad:
            e = bad[0]
            text = (e.get("error_msg") or e.get("message") or e.text or "").strip()
            first = text.splitlines()[0] if text else "(no message)"
            failures.append((case.get("name"),
                             f"{e.get('error_type') or 'failure'}: {first}"))
    return Result(tests, failures, elapsed, log, launched=True)


def row(mark, label, result):
    return f"  {mark:>6}  {label:<30} {result.summary():<26} {result.seconds:5.1f}s"


def main():
    tb = sys.argv[1] if len(sys.argv) > 1 else "test_adder"

    print(RULE)
    print(f" CHECK   testbench: {tb}      simulator: icarus")
    print(RULE)

    good = run_sim(tb, os.path.join(HERE, "src"), os.path.join(HERE, "build", "good"))
    print(row("ok" if good.all_passed else "FAIL", "src/  the good adder", good))
    if not good.launched:
        print(THIN)
        print(" The simulator never produced a results file. That is a setup problem,")
        print(" not a test failure. The last 20 lines of its output:")
        print(THIN)
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        return 1
    for name, msg in good.failures:
        print(f"        {name}")
        print(f"            {msg[:90]}")

    bad = run_sim(tb, os.path.join(HERE, "broken"), os.path.join(HERE, "build", "broken"))
    caught = bad.launched and bad.tests > 0 and bool(bad.failures)
    print(row("caught" if caught else "MISSED", "broken/  carry-in dropped", bad))
    for name, msg in bad.failures[:4]:
        print(f"        {name}")
        print(f"            {msg[:90]}")

    print(THIN)
    if good.all_passed and caught:
        print(" VERDICT: PASS")
        print("   Your testbench passes the good adder and catches the broken one.")
        print("   That is a test worth committing: it will still catch this bug in")
        print("   a year, on a rewrite, done by somebody who has never met you.")
        print(RULE)
        return 0

    if not good.all_passed:
        print(" VERDICT: FAIL -- your testbench does not pass the GOOD adder.")
        print("   Fix that first. Either the test expects the wrong thing, or you")
        print("   have found a real bug in an adder that is supposed to be correct.")
        print("   Run 'make sim' on its own to see the whole failure.")
    else:
        print(" VERDICT: FAIL -- your testbench passes the broken adder too.")
        print("   broken/ripple4.sv drops the carry-in on the way into slice 0, so")
        print("   every vector with cin = 1 comes out one too small. Every vector")
        print("   with cin = 0 is perfectly correct.")
        print("   Look at the third column of your stimulus. If cin is 0 in every")
        print("   row, this bug is not reachable by anything you drove.")
    print(RULE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
