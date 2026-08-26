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

────────────────────────────────────────────────────────────────────────────
AND THREE THINGS THIS SCRIPT REFUSES TO CALL A PASS
────────────────────────────────────────────────────────────────────────────
1.  A test that BLEW UP.  `NameError` is not a caught bug.  An exception that
    is not an AssertionError means Python stopped before your comparison
    happened, so the run says nothing about the adder.  `verdict.py` is where
    the two are told apart, and it is worth reading.

2.  A test that never RAN.  Every test skipped is not "all tests passed".

3.  Half the TODO.  The TODO in `t02` is two changes -- sweep `cin`, and
    collect the bad vectors instead of asserting on the first one -- and
    doing only the first gets you a red `broken/` row for the wrong reason.
    Both halves are measured here, in vectors driven, and the verdict names
    whichever one is missing.
"""

import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.abspath(os.path.join(HERE, "..", "common"))
sys.path.insert(0, COMMON)

import verdict as V                              # noqa: E402

RULE = "=" * 72
THIN = "-" * 72

# 4 + 4 + 1 = 9 bits of input on this module, so 2**9 of them.  The whole lab
# is this number.
SPACE = 512

_CHECKED = re.compile(r"checked\s+(\d+)")


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
        return V.not_launched(elapsed, log)
    return V.read_results(results, elapsed, log)


def vectors_driven(result):
    """How many input vectors this run actually put on the adder.

    Two independent measurements, and the larger wins, so that breaking one of
    them cannot silently understate the answer:

      * simulated time.  `apply()` advances time by 1 ns per vector, so the
        run's total sim_time_ns IS the vector count. It is in results.xml and
        the testbench cannot forget to report it.
      * the testbench's own `checked N` log line, if it got far enough to
        print one. A test that stops at the first bad vector never does.
    """
    from_time = int(result.sim_time_ns)
    from_log = max((int(m) for m in _CHECKED.findall(result.log)), default=0)
    return max(from_time, from_log)


def row(mark, label, result):
    return f"  {mark:>6}  {label:<30} {result.summary():<30} {result.seconds:5.1f}s"


def main():
    tb = sys.argv[1] if len(sys.argv) > 1 else "test_adder"

    print(RULE)
    print(f" CHECK   testbench: {tb}      simulator: icarus")
    print(RULE)

    good = run_sim(tb, os.path.join(HERE, "src"), os.path.join(HERE, "build", "good"))
    print(row(good.mark("pass"), "src/  the good adder", good))
    if not good.launched:
        print(THIN)
        print(" The simulator never produced a results file. That is a setup problem,")
        print(" not a test failure. The last 20 lines of its output:")
        print(THIN)
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        print(RULE)
        return 1
    V.report_problems(good)

    # A testbench that blew up on the GOOD adder is not a testbench yet, and
    # running it against the broken one would only produce a second crash to
    # misread. Stop here and say what happened.
    if good.broken:
        print(THIN)
        V.broken_testbench_verdict(good, "the good adder in src/")
        print(RULE)
        return 1
    if good.ran == 0:
        print(THIN)
        V.no_tests_ran_verdict(good)
        print(RULE)
        return 1

    bad = run_sim(tb, os.path.join(HERE, "broken"), os.path.join(HERE, "build", "broken"))
    print(row(bad.mark("fail"), "broken/  carry-in dropped", bad))
    V.report_problems(bad, limit=4)

    good_vectors = vectors_driven(good)
    bad_vectors = vectors_driven(bad)

    print(THIN)

    # ── the ways this is not a pass, most fundamental first ─────────────────

    if bad.broken:
        V.broken_testbench_verdict(bad, "the broken adder in broken/")
        print("")
        print("   Note that these same tests passed on the good adder. A test")
        print("   that only crashes when the design is wrong is usually a")
        print("   crash in the failure path -- the message you build when the")
        print("   comparison fails. That path has to work too; it is the half")
        print("   of the test anybody actually reads.")
        print(RULE)
        return 1

    if not good.all_passed:
        print(" VERDICT: FAIL -- your testbench does not pass the GOOD adder.")
        print("   Fix that first. Either the test expects the wrong thing, or you")
        print("   have found a real bug in an adder that is supposed to be correct.")
        print("   Run 'make sim' on its own to see the whole failure.")
        print(RULE)
        return 1

    if not bad.caught:
        if bad.ran == 0:
            V.no_tests_ran_verdict(bad)
            print(RULE)
            return 1
        print(" VERDICT: FAIL -- your testbench passes the broken adder too.")
        print("   broken/ripple4.sv drops the carry-in on the way into slice 0, so")
        print("   every vector with cin = 1 comes out one too small. Every vector")
        print("   with cin = 0 is perfectly correct.")
        print("   Look at the third column of your stimulus. If cin is 0 in every")
        print(f"   row, this bug is not reachable by anything you drove -- and you")
        print(f"   drove {good_vectors} of the {SPACE} vectors this module has.")
        print(RULE)
        return 1

    # ── the bug is caught. Was it caught by the test the lab asked for? ─────

    if good_vectors < SPACE:
        print(" VERDICT: FAIL -- the first half of the TODO is not done.")
        print(f"   On the good adder your tests drove {good_vectors} vectors. This")
        print(f"   module has {SPACE}: a, b and cin are 4 + 4 + 1 = 9 bits, and")
        print(f"   2**9 = {SPACE}.")
        print("")
        print("   Something in your run does catch the broken adder, so this is")
        print("   not a failure of nerve -- it is a failure of coverage, and the")
        print("   two look identical from a green run. Add the third loop:")
        print("")
        print("       for cin in range(2):")
        print("           for a in range(16):")
        print("               for b in range(16):")
        print("")
        print(f"   and make `checked` come out at {SPACE}.")
        print(RULE)
        return 1

    if bad_vectors < SPACE:
        print(" VERDICT: FAIL -- the second half of the TODO is not done.")
        print(f"   You swept cin: on the good adder you drove all {SPACE} vectors.")
        print(f"   On the broken adder you drove {bad_vectors} and then stopped,")
        print("   because you are still asserting on the first vector that is")
        print("   wrong instead of collecting them.")
        print("")
        print("   That is the change the TODO calls 'the one that turns a failing")
        print("   test into a diagnosis', and it is the whole of Step 4:")
        print("")
        print("       bad = []")
        print("       for cin in range(2):")
        print("           for a in range(16):")
        print("               for b in range(16):")
        print("                   ...")
        print("                   if got != want:")
        print("                       bad.append((a, b, cin, got, want))")
        print("       assert not bad, f'{len(bad)} of {checked} vectors are wrong'")
        print("")
        print("   'It is wrong' tells you to start looking. '256 of 512 are wrong'")
        print("   tells you the fault tracks an input that is high in exactly half")
        print(f"   the vectors, and this module has one such input. You stopped at")
        print(f"   vector {bad_vectors}, so you cannot know that number yet.")
        print(RULE)
        return 1

    print(" VERDICT: PASS")
    print(f"   {SPACE} vectors on the good adder, all correct.")
    print(f"   {SPACE} vectors on the broken one, and the failure is a count, not")
    print("   an anecdote:")
    for name, msg in bad.failures[:2]:
        print(f"       {name}: {msg[:80]}")
    print("   That is a test worth committing: it will still catch this bug in")
    print("   a year, on a rewrite, done by somebody who has never met you.")
    print(RULE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
