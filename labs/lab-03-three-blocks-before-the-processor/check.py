"""
DD104 Lab 03 — the verdict, at unit level.

    make check                test_alu against the golden ALU and B01
    make check BUG=B03        ... and B03
    make check-alu-bugs       all three ALU bugs at once

Same two-sided verdict as every other lab, pointed at one module instead of the
whole chip:

    it must PASS on the golden ALU       -- or you are testing the wrong thing
    it must FAIL on a broken one         -- or you are not testing anything

The broken ALUs come from `../common/bugs.py`, which is the same catalogue the
processor-level labs use.  `inject.py` refuses to patch a line whose text has
drifted, so a "broken" core here is always actually broken.
"""

import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.abspath(os.path.join(HERE, "..", "common"))
sys.path.insert(0, COMMON)

import inject                                   # noqa: E402
from bugs import BUGS, TEACHES, resolve         # noqa: E402

RULE = "=" * 72
THIN = "-" * 72

# The three catalogue bugs that live inside the ALU module itself.  Everything
# else in the catalogue is in the control path, where a unit test of the ALU
# cannot see it — which is the honest limit of unit testing and is worth
# saying out loud rather than discovering.
ALU_BUGS = ["B01", "B02", "B03"]


class Result:
    def __init__(self, tests, failures, seconds, log, launched):
        self.tests, self.failures = tests, failures
        self.seconds, self.log, self.launched = seconds, log, launched

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


def run_sim(tb, toplevel, rtl_dir, build_dir):
    results = os.path.join(build_dir, "results.xml")
    os.makedirs(build_dir, exist_ok=True)
    if os.path.exists(results):
        os.remove(results)

    cmd = [
        "make", "-f", os.path.join(COMMON, "sim.mk"), "sim",
        f"COMMON={COMMON}", f"TB={tb}", "SIM=icarus", f"TOPLEVEL={toplevel}",
        f"VERILOG_SOURCES={os.path.join(rtl_dir, 'simproc_system.sv')}",
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
            failures.append((case.get("name"),
                             text.splitlines()[0] if text else "(no message)"))
    return Result(tests, failures, elapsed, log, launched=True)


def row(mark, label, r):
    return f"  {mark:>6}  {label:<34} {r.summary():<26} {r.seconds:5.1f}s"


def one(tb, toplevel, bug):
    print(RULE)
    print(f" CHECK   testbench: {tb}   module under test: {toplevel}")
    print(RULE)

    good = run_sim(tb, toplevel, os.path.join(COMMON, "rtl"),
                   os.path.join(HERE, "build", "golden"))
    print(row("ok" if good.all_passed else "FAIL", f"the golden {toplevel}", good))
    if not good.launched:
        print(THIN)
        print(" The simulator never produced a results file. That is a setup problem,")
        print(" not a test failure. The last 20 lines of its output:")
        print(THIN)
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        return False
    for name, msg in good.failures:
        print(f"        {name}\n            {msg[:90]}")

    name = resolve(bug)
    rtl = inject.build(name, os.path.join(HERE, "build", "broken", name))
    bad = run_sim(tb, toplevel, rtl,
                  os.path.join(HERE, "build", "broken", name, "run"))
    caught = bad.launched and bad.tests > 0 and bool(bad.failures)
    print(row("caught" if caught else "MISSED", name, bad))
    for tname, msg in bad.failures[:4]:
        print(f"        {tname}\n            {msg[:90]}")

    print(THIN)
    if good.all_passed and caught:
        print(" VERDICT: PASS")
        print(f"   {tb} passes the golden {toplevel} and catches {name}.")
        print(f"   That bug teaches: {TEACHES[name]}")
    elif not good.all_passed:
        print(f" VERDICT: FAIL -- {tb} does not pass the GOLDEN {toplevel}.")
        print("   Fix that first. Either the test expects the wrong thing, or")
        print("   `spec()` and the RTL disagree and one of them is right.")
    else:
        print(f" VERDICT: FAIL -- {tb} passes {name} too.")
        print(f"   That bug hides behind: {BUGS[name]['hides_behind']}")
        print("   Write a test whose stimulus does not do that.")
    print(RULE)
    return good.all_passed and caught


def alu_sweep(tb, toplevel):
    print(RULE)
    print(f" CHECK-ALU-BUGS   testbench: {tb}   module under test: {toplevel}")
    print(RULE)
    good = run_sim(tb, toplevel, os.path.join(COMMON, "rtl"),
                   os.path.join(HERE, "build", "golden"))
    print(row("ok" if good.all_passed else "FAIL", f"the golden {toplevel}", good))
    if not good.all_passed:
        print(THIN)
        print(" Stopping: the testbench has to pass the golden module before")
        print(" 'does it catch bugs?' is a meaningful question.")
        print(RULE)
        return False

    print(THIN)
    missed = []
    for b in ALU_BUGS:
        name = resolve(b)
        rtl = inject.build(name, os.path.join(HERE, "build", "broken", name))
        r = run_sim(tb, toplevel, rtl,
                    os.path.join(HERE, "build", "broken", name, "run"))
        hit = r.launched and bool(r.failures)
        if not hit:
            missed.append(name)
        print(row("caught" if hit else "MISSED", name, r))

    print(THIN)
    print(f" {len(ALU_BUGS) - len(missed)} of {len(ALU_BUGS)} ALU bugs caught.")
    if missed:
        for m in missed:
            print(f"   still hiding: {m}")
            print(f"      behind: {BUGS[m]['hides_behind']}")
    else:
        print(" Every bug the catalogue puts inside the ALU. The other ten are")
        print(" in the control path around it, where a unit test of the ALU")
        print(" cannot reach them -- that is Lab 04.")
    print(RULE)
    return not missed


if __name__ == "__main__":
    args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    mode = sys.argv[1] if sys.argv[1:] and "=" not in sys.argv[1] else "one"
    tb = args.get("TB", "test_alu")
    toplevel = args.get("TOPLEVEL", "ALU")
    ok = (alu_sweep(tb, toplevel) if mode == "sweep"
          else one(tb, toplevel, args.get("BUG", "B01")))
    sys.exit(0 if ok else 1)
