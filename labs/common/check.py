"""
DD104 — the verdict.

    make check                 your testbench vs. the good core and one broken one
    make check-all             your testbench vs. all thirteen broken cores
    make check BUG=B07         pick which broken core

────────────────────────────────────────────────────────────────────────────
WHY THIS EXISTS
────────────────────────────────────────────────────────────────────────────
Here is a testbench:

    @cocotb.test()
    async def it_works(dut):
        pass

It passes.  It passes on the good core, on a core whose SUB is backwards, on a
core that writes every result into the wrong register, and on a core that
never finishes an instruction.  It passes on everything, which means it
distinguishes nothing, which means it is worth nothing.

That is not a strawman.  SimProc shipped with `test/test.py`, and what it
does is set `ui_in = 1`, wait 100 clock cycles, and assert `uo_out == 3`.
Decoded against the pin map, `3` is `uart_tx = 1` (an idle serial line),
`halt = 1` (the core sitting in IDLE) and `done = 0`.  **It asserts that the
processor is not running.**  It sends no command, loads no program and
executes no instruction — and it passes against every one of the thirteen
deliberately broken cores in this course.  Run `make shuttle` and watch.

So "my tests pass" is not a result.  The result is two-sided:

    it must PASS on the good core          — or you are testing the wrong thing
    it must FAIL on the broken one         — or you are not testing anything

`check.py` runs both and says which.  That is the verdict.

────────────────────────────────────────────────────────────────────────────
AND "FAILED" IS NOT THE SAME WORD AS "BLEW UP"
────────────────────────────────────────────────────────────────────────────
A test that raises `NameError` has not caught a bug.  It stopped before the
comparison happened, so it says nothing at all about the core it was pointed
at -- and it would say the same nothing about every other core in the
catalogue.  Counting one of those as a catch is how a grader hands out a PASS
for a testbench that does not run.  `verdict.py` is where the two are told
apart, and every DD104 checker reads it from there.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import inject                                   # noqa: E402
import verdict as V                             # noqa: E402
from bugs import BUGS, TEACHES, names, resolve  # noqa: E402

RULE = "=" * 72
THIN = "-" * 72


def run_sim(tb, rtl_dir, build_dir, sim="icarus", lab_dir=None, plusargs=None):
    """Run one cocotb simulation and read the results file."""
    lab_dir = lab_dir or os.getcwd()
    results = os.path.join(build_dir, "results.xml")
    os.makedirs(build_dir, exist_ok=True)
    if os.path.exists(results):
        os.remove(results)

    cmd = [
        "make", "-f", os.path.join(HERE, "sim.mk"), "sim",
        f"COMMON={HERE}", f"TB={tb}", f"SIM={sim}", f"RTL_DIR={rtl_dir}",
        f"SIM_BUILD={os.path.join(build_dir, 'sim')}",
        f"COCOTB_RESULTS_FILE={results}",
    ]
    if plusargs:
        cmd.append(f"COCOTB_PLUSARGS={plusargs}")

    t0 = time.time()
    proc = subprocess.run(cmd, cwd=lab_dir, capture_output=True, text=True)
    elapsed = time.time() - t0
    log = proc.stdout + proc.stderr

    if not os.path.exists(results):
        return V.not_launched(elapsed, log)
    return V.read_results(results, elapsed, log)


def golden_rtl():
    return os.path.join(HERE, "rtl")


def broken_rtl(bug, lab_dir):
    """Build the broken core into the lab's build/ directory."""
    name = resolve(bug)
    out = os.path.join(lab_dir, "build", "broken", name)
    return name, inject.build(name, out_dir=out)


# ── the report ───────────────────────────────────────────────────────────────

def line(label, result, expectation):
    """One row of the report.

    `expectation` is 'pass' (the golden core: your tests must all pass) or
    'fail' (a broken core: a CHECK must fire, or the bug went undetected).

    A run in which a test blew up is neither, and is marked BROKEN. It is
    never `ok` and it is never `caught`: an exception that is not an
    AssertionError compared nothing, so it is not evidence about this core.
    """
    ok = result.all_passed if expectation == "pass" else result.caught
    mark = result.mark(expectation)
    return f"  {mark:>6}  {label:<34} {result.summary():<30} {result.seconds:5.1f}s", ok


def check_one(tb, bug, sim, lab_dir, verbose=False):
    print(RULE)
    print(f" CHECK   testbench: {tb}      simulator: {sim}")
    print(RULE)

    good = run_sim(tb, golden_rtl(), os.path.join(lab_dir, "build", "golden"),
                   sim=sim, lab_dir=lab_dir)
    row, good_ok = line("the golden core", good, "pass")
    print(row)
    if not good.launched:
        print(THIN)
        print(" The simulator never produced a results file. That is a setup")
        print(" problem, not a test failure. The last 20 lines of its output:")
        print(THIN)
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        return False
    V.report_problems(good)
    if good.broken:
        print(THIN)
        V.broken_testbench_verdict(good, "the golden core")
        print(RULE)
        return False
    if good.ran == 0:
        print(THIN)
        V.no_tests_ran_verdict(good)
        print(RULE)
        return False

    name, rtl = broken_rtl(bug, lab_dir)
    bad = run_sim(tb, rtl, os.path.join(lab_dir, "build", "broken", name, "run"),
                  sim=sim, lab_dir=lab_dir)
    row, bad_ok = line(name, bad, "fail")
    print(row)
    V.report_problems(bad, limit=4)

    print(THIN)
    if bad.broken:
        V.broken_testbench_verdict(bad, name)
        print("")
        print("   These same tests passed on the golden core, so the crash is in")
        print("   a path only a wrong answer reaches -- usually the message you")
        print("   build when the comparison fails. That path has to work too.")
    elif good_ok and bad_ok:
        print(f" VERDICT: PASS")
        print(f"   Your testbench passes the good core, and on {name} a check FIRED:")
        for tname, msg in bad.failures[:2]:
            print(f"       {tname}: {msg[:76]}")
        print(f"   That bug teaches: {TEACHES[name]}")
    elif not good_ok:
        print(f" VERDICT: FAIL — your testbench does not pass the GOLDEN core.")
        print(f"   Fix that first. Either the test expects the wrong thing, or")
        print(f"   the harness is being used in a way the chip does not support.")
        print(f"   Run 'make sim' on its own to see the full failure.")
    elif bad.ran == 0:
        V.no_tests_ran_verdict(bad)
    else:
        print(f" VERDICT: FAIL — your testbench passes {name} too.")
        print(f"   A test that passes on a broken core is not testing that core.")
        print(f"   That bug hides behind: {BUGS[name]['hides_behind']}")
        print(f"   Write a test whose stimulus does not do that.")
    print(RULE)
    if verbose:
        print(bad.log)
    return good_ok and bad_ok and not bad.broken


def check_all(tb, sim, lab_dir):
    print(RULE)
    print(f" CHECK-ALL   testbench: {tb}      simulator: {sim}")
    print(RULE)

    good = run_sim(tb, golden_rtl(), os.path.join(lab_dir, "build", "golden"),
                   sim=sim, lab_dir=lab_dir)
    row, good_ok = line("the golden core", good, "pass")
    print(row)
    V.report_problems(good)
    if good.broken:
        print(THIN)
        V.broken_testbench_verdict(good, "the golden core")
        print(RULE)
        return False
    if good.ran == 0:
        print(THIN)
        V.no_tests_ran_verdict(good)
        print(RULE)
        return False
    if not good_ok:
        print(THIN)
        print(" Stopping: the testbench must pass the golden core before")
        print(" 'does it catch bugs?' is a meaningful question.")
        print(RULE)
        return False
    print(THIN)

    caught, missed, blew_up = [], [], []
    for bug in names():
        name, rtl = broken_rtl(bug, lab_dir)
        r = run_sim(tb, rtl, os.path.join(lab_dir, "build", "broken", name, "run"),
                    sim=sim, lab_dir=lab_dir)
        if r.broken:
            blew_up.append((name, r))
            who = r.errors[0][0]
        elif r.caught:
            caught.append(name)
            who = r.failures[0][0]
        else:
            missed.append(name)
            who = ""
        print(f"  {r.mark('fail'):>6}  tier {BUGS[name]['tier']}  "
              f"{name:<34} {who[:22]:<22} {r.seconds:5.1f}s")

    print(THIN)

    # A run in which a test blew up is not a count of anything, so do not
    # print a count. `12 of 13 caught` would be a claim about the design;
    # a NameError is a claim about the testbench and nothing else.
    if blew_up:
        print(f" NO COUNT. {len(blew_up)} of the {len(BUGS)} runs did not finish:")
        for name, r in blew_up:
            for tname, msg in r.errors[:1]:
                print(f"   {name}: {tname} BLEW UP")
                print(f"      {msg[:80]}")
        print("")
        print(" Those tests raised before they compared anything, so they are not")
        print(" catches -- on these cores or on any other. There is no score to")
        print(" report until the testbench runs to the end. `make sim` on its own")
        print(" prints the traceback.")
        print(RULE)
        return False

    print(f" {len(caught)} of {len(BUGS)} caught.")
    if missed:
        print(f" Still hiding from this testbench:")
        for m in missed:
            print(f"   {m}")
            print(f"      hides behind: {BUGS[m]['hides_behind']}")
    else:
        print(" Every bug in the catalogue, every one of them caught by a check")
        print(" that fired. Nothing in this course hides from this testbench any")
        print(" more.")
    print(RULE)
    return not missed


def check_shuttle(sim, lab_dir):
    """Run the test SimProc actually shipped with, against everything."""
    tb = "test_shuttle"
    print(RULE)
    print(" THE TEST THIS CHIP SHIPPED WITH")
    print(RULE)
    print(" test/test.py, from the SimProc repository, untouched. It sets")
    print(" ui_in = 1, waits 100 clock cycles, and asserts uo_out == 3.")
    print(" Decoded: uart_tx = 1 (idle), halt = 1 (IDLE), done = 0.")
    print(" It asserts that the processor is NOT RUNNING.")
    print(THIN)

    good = run_sim(tb, golden_rtl(), os.path.join(lab_dir, "build", "shuttle-golden"),
                   sim=sim, lab_dir=lab_dir)
    def word(r):
        # This demonstration prints PASS/FAIL rather than ok/FAIL because the
        # point being made is "the shipped test passes on all of them". BROKEN
        # would mean test_shuttle.py itself had stopped working.
        return "BROKEN" if r.broken else ("PASS" if r.all_passed else "FAIL")

    print(f"  {word(good):>6}  "
          f"{'the golden core':<42} {good.seconds:5.1f}s")

    survived = 0
    for bug in names():
        name, rtl = broken_rtl(bug, lab_dir)
        r = run_sim(tb, rtl, os.path.join(lab_dir, "build", "broken", name, "shuttle"),
                    sim=sim, lab_dir=lab_dir)
        ok = r.all_passed
        survived += ok
        print(f"  {word(r):>6}  {name:<42} {r.seconds:5.1f}s")

    print(THIN)
    print(f" {survived} of {len(BUGS)} deliberately broken processors pass the")
    print(f" only test this chip has.")
    print(RULE)
    return survived


def main():
    ap = argparse.ArgumentParser(description="DD104 — pass on the good core, fail on the bad one")
    ap.add_argument("--tb", default="test_example", help="test module name")
    ap.add_argument("--bug", default="B01", help="which broken core (name or prefix)")
    ap.add_argument("--sim", default="icarus", help="icarus (default) or verilator")
    ap.add_argument("--dir", default=None, help="the lab directory")
    ap.add_argument("--all", action="store_true", help="check against all 13 bugs")
    ap.add_argument("--shuttle", action="store_true", help="run the shipped test on everything")
    ap.add_argument("-v", "--verbose", action="store_true", help="print the broken run's log")
    args = ap.parse_args()

    lab_dir = os.path.abspath(args.dir or os.getcwd())
    if shutil.which("make") is None:
        sys.exit("check.py needs `make`, and it is not on PATH. Are you in the workbench container?")

    if args.shuttle:
        check_shuttle(args.sim, lab_dir)
        return 0                     # this one is a demonstration, not a grade
    ok = (check_all(args.tb, args.sim, lab_dir) if args.all
          else check_one(args.tb, args.bug, args.sim, lab_dir, args.verbose))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
