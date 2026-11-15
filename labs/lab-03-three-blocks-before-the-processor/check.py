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

And a bug is only "caught" if a CHECK fired.  A test that raised `NameError`
did not catch anything -- it stopped before the comparison happened, and it
would have raised on the golden ALU too if the golden ALU had ever reached
that line.  `../common/verdict.py` is where the two are told apart; this file
used to count them the same and told a student `3 of 3 ALU bugs caught` about
a testbench that crashed three times.
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.abspath(os.path.join(HERE, "..", "common"))
sys.path.insert(0, COMMON)

import inject                                   # noqa: E402
import verdict as V                             # noqa: E402
from bugs import BUGS, TEACHES, resolve         # noqa: E402

RULE = "=" * 72
THIN = "-" * 72

# The three catalogue bugs that live inside the ALU module itself.  Everything
# else in the catalogue is in the control path, apart from B12 in the UART
# receiver, and a unit test of the ALU cannot see any of it — which is the
# honest limit of unit testing and is worth saying out loud rather than
# discovering.
ALU_BUGS = ["B01", "B02", "B03"]


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
        return V.not_launched(elapsed, log)
    return V.read_results(results, elapsed, log)


def row(mark, label, r):
    return f"  {mark:>6}  {label:<34} {r.summary():<30} {r.seconds:5.1f}s"


def golden_run(tb, toplevel):
    """The golden module, and the three ways it can stop the check dead."""
    good = run_sim(tb, toplevel, os.path.join(COMMON, "rtl"),
                   os.path.join(HERE, "build", "golden"))
    print(row(good.mark("pass"), f"the golden {toplevel}", good))

    if not good.launched:
        print(THIN)
        print(" The simulator never produced a results file. That is a setup problem,")
        print(" not a test failure. The last 20 lines of its output:")
        print(THIN)
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        print(RULE)
        return good, False

    V.report_problems(good)

    if good.broken:
        print(THIN)
        V.broken_testbench_verdict(good, f"the golden {toplevel}")
        print(RULE)
        return good, False
    if good.ran == 0:
        print(THIN)
        V.no_tests_ran_verdict(good)
        print(RULE)
        return good, False
    return good, True


def one(tb, toplevel, bug):
    print(RULE)
    print(f" CHECK   testbench: {tb}   module under test: {toplevel}")
    print(RULE)

    good, usable = golden_run(tb, toplevel)
    if not usable:
        return False

    name = resolve(bug)
    rtl = inject.build(name, os.path.join(HERE, "build", "broken", name))
    bad = run_sim(tb, toplevel, rtl,
                  os.path.join(HERE, "build", "broken", name, "run"))
    print(row(bad.mark("fail"), name, bad))
    V.report_problems(bad, limit=4)

    print(THIN)
    if bad.broken:
        V.broken_testbench_verdict(bad, name)
        print("")
        print(f"   These same tests passed on the golden {toplevel}, so the crash is")
        print("   in a path only a wrong answer reaches -- almost always the")
        print("   message you build when the comparison fails. That path has to")
        print("   work too; it is the half of the test anybody actually reads.")
        print(RULE)
        return False

    if not good.all_passed:
        print(f" VERDICT: FAIL -- {tb} does not pass the GOLDEN {toplevel}.")
        print("   Fix that first. Either the test expects the wrong thing, or")
        print("   `spec()` and the RTL disagree and one of them is right.")
        print(RULE)
        return False

    if not bad.caught:
        if bad.ran == 0:
            V.no_tests_ran_verdict(bad)
        else:
            print(f" VERDICT: FAIL -- {tb} passes {name} too.")
            print(f"   That bug hides behind: {BUGS[name]['hides_behind']}")
            print("   Write a test whose stimulus does not do that.")
        print(RULE)
        return False

    print(" VERDICT: PASS")
    print(f"   {tb} passes the golden {toplevel}, and on {name} a check FIRED:")
    for tname, msg in bad.failures[:2]:
        print(f"       {tname}: {msg[:78]}")
    print(f"   That bug teaches: {TEACHES[name]}")
    print(RULE)
    return True


def alu_sweep(tb, toplevel):
    print(RULE)
    print(f" CHECK-ALU-BUGS   testbench: {tb}   module under test: {toplevel}")
    print(RULE)

    good, usable = golden_run(tb, toplevel)
    if not usable:
        return False
    if not good.all_passed:
        print(THIN)
        print(" Stopping: the testbench has to pass the golden module before")
        print(" 'does it catch bugs?' is a meaningful question.")
        print(RULE)
        return False

    print(THIN)
    missed, blew_up = [], []
    for b in ALU_BUGS:
        name = resolve(b)
        rtl = inject.build(name, os.path.join(HERE, "build", "broken", name))
        r = run_sim(tb, toplevel, rtl,
                    os.path.join(HERE, "build", "broken", name, "run"))
        if r.broken:
            blew_up.append((name, r))
        elif not r.caught:
            missed.append(name)
        print(row(r.mark("fail"), name, r))

    print(THIN)

    # A run in which a test blew up is not a count of anything. Say that
    # instead of a number, because the number would be a lie: an exception
    # that is not an AssertionError compared nothing.
    if blew_up:
        print(f" NO COUNT. {len(blew_up)} of the {len(ALU_BUGS)} runs did not finish:")
        for name, r in blew_up:
            for tname, msg in r.errors[:2]:
                print(f"   {name}: {tname} BLEW UP")
                print(f"      {msg[:80]}")
        print("")
        print(" A test that raises NameError, TypeError or AttributeError stopped")
        print(" before it compared anything. It is not a caught bug -- it is not")
        print(" even a test yet -- so this sweep has no score to report. Fix the")
        print(" testbench, then run it again.")
        print(RULE)
        return False

    print(f" {len(ALU_BUGS) - len(missed)} of {len(ALU_BUGS)} ALU bugs caught.")
    if missed:
        for m in missed:
            print(f"   still hiding: {m}")
            print(f"      behind: {BUGS[m]['hides_behind']}")
    else:
        print(" Every bug the catalogue puts inside the ALU, and every one of them")
        print(" caught by a check that fired, not by a testbench that crashed.")
        print(" Of the other ten, nine are in the control path around it and one is")
        print(" in the UART receiver, where a unit test of the ALU cannot reach")
        print(" them -- that is Labs 04 to 06.")
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
