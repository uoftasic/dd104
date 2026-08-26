"""
DD104 — the bug hunt.

    make new        deal a mystery core.  You are not told which bug it is.
    make hunt       your testbench against that core -- the loop you live in
    make probe      the same run, showing the simulator's own output
    make verdict    the grade
    make reveal     give up, and be told the name

────────────────────────────────────────────────────────────────────────────
THE GRADE HAS THREE ROWS, AND THEY ARE IN THIS ORDER ON PURPOSE
────────────────────────────────────────────────────────────────────────────

    1.  your testbench on the GOLDEN core          must PASS
    2.  your testbench on the ORIGINAL mystery     must FAIL
    3.  your testbench on core/ as it stands now   must PASS

Row 2 is the deliverable.  A patch is a thing one person did once; a test that
fails on the old core is the thing that stops the bug coming back in a year,
in a rewrite, done by somebody who has never heard of you.  Rows 1 and 3
without row 2 is a fix nobody can prove, and this script will not give you a
PASS for it.

Row 2 is always rebuilt fresh from the catalogue, not read from `core/`.  You
cannot get a green row 2 by editing the file the test runs against.

And row 2 is green only if a CHECK FIRED.  A test that raised `NameError`,
`TypeError` or `AttributeError` stopped before it compared anything: it did
not catch the bug, it crashed, and it would crash the same way on a perfectly
correct processor.  Such a row is marked BROKEN, never `caught`, and the
verdict says which exception and where.  `../common/verdict.py` is where the
two are told apart.
────────────────────────────────────────────────────────────────────────────
"""

import base64
import os
import random
import shlex
import shutil
import subprocess
import textwrap
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

CORE = os.path.join(HERE, "core")               # the student's editable copy
SEAL = os.path.join(CORE, ".sealed")            # which bug it was
                                                # (inside core/, so that
                                                #  `make clean` cannot
                                                #  lose your hunt)

# ── the pool this lab deals from ────────────────────────────────────────────
POOL = ["B08", "B13"]
POOL_NOTE = ('Neither one changes a single register, flag, PC value or byte of '
             'memory. Every architectural result both of these processors produce is correct. '
             'Your Lab 03 and Lab 04 testbenches pass on both of them, and so does '
             'the golden model. Only the protocol is wrong.')


def run_sim(tb, rtl_dir, build_dir, sim="icarus", stream=False):
    """Run one simulation.  With stream=True the simulator's own output goes
    to your terminal as it happens -- every print() and every dut._log line.

    Quiet is the default because the verdict is a table and a table with 200
    lines of Icarus in the middle of it is not a table.  Quiet is NOT the
    default because you are not supposed to see this; see `make probe`."""
    results = os.path.join(build_dir, "results.xml")
    os.makedirs(build_dir, exist_ok=True)
    if os.path.exists(results):
        os.remove(results)

    cmd = [
        "make", "-f", os.path.join(COMMON, "sim.mk"), "sim",
        f"COMMON={COMMON}", f"TB={tb}", f"SIM={sim}", f"RTL_DIR={rtl_dir}",
        f"SIM_BUILD={os.path.join(build_dir, 'sim')}",
        f"COCOTB_RESULTS_FILE={results}",
    ]
    t0 = time.time()
    if stream:
        # Line-buffered passthrough: you see it while it runs, AND we keep a
        # copy, so the "simulator never launched" report below still works.
        head, tail = cmd[:4], cmd[4:]
        print(f"  $ cd {shlex.quote(HERE)} && \\")
        print("    " + " ".join(shlex.quote(c) for c in head) + " \\")
        for i, a in enumerate(tail):
            print(f"      {shlex.quote(a)}" + (" \\" if i < len(tail) - 1 else ""))
        print(THIN)
        proc = subprocess.Popen(cmd, cwd=HERE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        chunks = []
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            chunks.append(line)
        proc.wait()
        log = "".join(chunks)
    else:
        proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        log = proc.stdout + proc.stderr
    elapsed = time.time() - t0

    if not os.path.exists(results):
        return V.not_launched(elapsed, log)
    return V.read_results(results, elapsed, log)


# ── the seal ────────────────────────────────────────────────────────────────

def seal(name):
    os.makedirs(os.path.dirname(SEAL), exist_ok=True)
    with open(SEAL, "w") as f:
        f.write("# DD104 -- which bug you were dealt, base64'd.\n"
                "# Decoding this costs you the lab. `make reveal` does it for\n"
                "# you when you have genuinely had enough, and says so on the\n"
                "# way past. It is an honour system and it is stated as one.\n")
        f.write(base64.b64encode(name.encode()).decode() + "\n")


def unseal():
    if not os.path.exists(SEAL):
        return None
    for line in open(SEAL):
        line = line.strip()
        if line and not line.startswith("#"):
            return base64.b64decode(line).decode()
    return None


def deal(which=None):
    """Pick a bug, write core/, seal the answer."""
    name = resolve(which) if which else resolve(random.choice(POOL))
    if os.path.exists(CORE):
        shutil.rmtree(CORE)
    tmp = os.path.join(HERE, "build", "dealt")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    rtl = inject.build(name, tmp)
    shutil.copytree(rtl, CORE)
    seal(name)

    print(RULE)
    print(" A MYSTERY CORE")
    print(RULE)
    print(" Written to core/: the two RTL files and the testbench wrapper.")
    print(" Exactly one line of simproc_system.sv differs from the golden core.")
    print("")
    print(f" It is one of {len(POOL)}: {', '.join(sorted(POOL))}.")
    for l in textwrap.wrap(POOL_NOTE, 68):
        print(f" {l}")
    print("")
    print(" You are not told which. Do not diff core/ against ../common/rtl/ --")
    print(" it works, it takes four seconds, and it skips the entire lab. The")
    print(" skill being built here is finding a bug in a design you cannot")
    print(" diff against a known-good one, which is every real design.")
    print("")
    print(" The loop:")
    print("   make hunt        your testbench against core/")
    print("   make verdict     the grade")
    print("   make new         deal a different one (this deletes core/)")
    print(RULE)
    return name


# ── the report ──────────────────────────────────────────────────────────────

def row(mark, label, r):
    return f"  {mark:>6}  {label:<42} {r.summary():<24} {r.seconds:5.1f}s"


def hunt(tb, sim="icarus", verbose=False):
    """Run the testbench against core/ and print what happened.  No grade.

    verbose=True (`make probe`, or `make hunt VERBOSE=1`) streams the
    simulator's own stdout, which is where your print() and dut._log lines
    are."""
    if not os.path.exists(CORE):
        print("There is no core/ yet. Run `make new` first.")
        return 1
    name = unseal()
    print(RULE)
    print(f" {'PROBE' if verbose else 'HUNT '}  testbench: {tb}   target: core/")
    print(RULE)
    if verbose:
        print(" Showing everything the simulator says. Your print() and dut._log")
        print(" lines are in here, in the order they happened.")
        print(THIN)
    r = run_sim(tb, CORE, os.path.join(HERE, "build", "hunt"),
                sim=sim, stream=verbose)
    if verbose:
        print(THIN)
    mark = "!" if not r.launched else r.mark("fail")
    print(row(mark if mark != "MISSED" else "quiet", "core/  the mystery", r))
    V.report_problems(r)
    print(THIN)
    if not r.launched:
        if verbose:
            print(" The simulator never produced a results file. That is a setup problem,")
            print(" not a test failure. Its output is above, in full.")
        else:
            print(" The simulator never produced a results file. That is a setup problem,")
            print(" not a test failure. The last 20 lines of its output:")
            for l in r.log.strip().splitlines()[-20:]:
                print("   " + l)
            print("")
            print(" `make probe` re-runs this with the whole log, not the last 20 lines.")
        print(RULE)
        return 1
    if r.broken:
        print(" One of your tests BLEW UP -- it raised something that is not an")
        print(" AssertionError, so it stopped before it compared anything. That")
        print(" is not a bug you found in this core; it is a bug in the test, and")
        print(" it would raise the same way on a perfectly correct processor.")
        print(" Fix it first: `make probe` shows the whole traceback.")
    elif r.failures:
        print(" Something in this core disagrees with your testbench. That is not")
        print(" yet a verdict -- your test could be wrong. `make verdict` runs it")
        print(" against the golden core too, which is what settles it.")
    elif r.ran == 0:
        print(" Nothing ran. Every test in the module was skipped or filtered out,")
        print(" so this core has not been tested at all -- check TB= and")
        print(" COCOTB_TESTCASE.")
    else:
        print(" Nothing your testbench drives can tell this core from a correct")
        print(" one. The bug is real and it is in there; your stimulus has not")
        print(" reached it yet. Widen the stimulus, not the assertions.")
    if not verbose:
        arg = "" if tb == "test_lab05" else f" TB={tb}"
        print("")
        print(" To WATCH it instead of being told about it -- every print(), every")
        print(" dut._log line, live, plus the command to run by hand:")
        print("")
        print(f"     make probe{arg}")
        print("")
        print(f" (`make hunt{arg} VERBOSE=1` is the same target. `make verdict")
        print("  VERBOSE=1` does it for all three rows of the grade.)")
    print(RULE)
    return 0


def verdict(tb, sim="icarus", verbose=False):
    name = unseal()
    if not os.path.exists(CORE) or name is None:
        print("There is no core/ yet. Run `make new` first.")
        return 1

    print(RULE)
    print(f" VERDICT   testbench: {tb}   simulator: {sim}")
    print(RULE)

    def banner(n, what):
        if verbose:
            print(THIN)
            print(f" row {n} -- {what}: the simulator's own output")
            print(THIN)

    banner(1, "the golden core")
    good = run_sim(tb, os.path.join(COMMON, "rtl"),
                   os.path.join(HERE, "build", "golden"),
                   sim=sim, stream=verbose)
    if verbose:
        print(THIN)
    print(row(good.mark("pass"),
              "1. the golden core          must PASS", good))
    if not good.launched:
        print(THIN)
        print(" The simulator never produced a results file. That is a setup problem,")
        print(" not a test failure. The last 20 lines of its output:")
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        print(RULE)
        return 1
    V.report_problems(good, limit=4)
    if good.broken:
        print(THIN)
        V.broken_testbench_verdict(good, "the golden core")
        print(RULE)
        return 1
    if good.ran == 0:
        print(THIN)
        V.no_tests_ran_verdict(good)
        print(RULE)
        return 1

    # Row 2 is rebuilt from the catalogue, never read from core/.
    fresh = inject.build(name, os.path.join(HERE, "build", "original"))
    banner(2, "the core you were dealt")
    orig = run_sim(tb, fresh, os.path.join(HERE, "build", "original", "run"),
                   sim=sim, stream=verbose)
    if verbose:
        print(THIN)
    caught = orig.caught
    print(row(orig.mark("fail"),
              "2. the core you were dealt  must FAIL", orig))
    V.report_problems(orig, limit=4)

    banner(3, "core/ as it stands now")
    fixed = run_sim(tb, CORE, os.path.join(HERE, "build", "fixed"),
                    sim=sim, stream=verbose)
    if verbose:
        print(THIN)
    print(row(fixed.mark("pass"),
              "3. core/ as it stands now   must PASS", fixed))
    V.report_problems(fixed, limit=4)

    print(THIN)

    # A run in which a test blew up is not a row of this table at all. It is
    # not a pass and it is not a catch: an exception that is not an
    # AssertionError compared nothing, so it is not evidence about any core.
    for r, where in ((orig, "the core you were dealt"),
                     (fixed, "core/ as it stands now")):
        if r.broken:
            V.broken_testbench_verdict(r, where)
            print("")
            print("   These same tests ran to the end on the golden core, so the")
            print("   crash is in a path only a wrong answer reaches -- usually")
            print("   the message you build when a comparison fails. That path is")
            print("   the half of the test a human actually reads. Fix it, then")
            print("   ask for the grade again.")
            print(RULE)
            return 1

    if good.all_passed and caught and fixed.all_passed:
        print(" VERDICT: PASS")
        print(f"   The bug was {name}.")
        print(f"   It hides behind: {BUGS[name]['hides_behind']}")
        print(f"   It teaches: {TEACHES[name]}")
        print("")
        print("   Row 2 is the part worth keeping. Commit that test.")
        print(RULE)
        return 0

    if not good.all_passed:
        print(" VERDICT: FAIL -- row 1. Your testbench does not pass the GOLDEN core.")
        print("   Nothing else is meaningful until it does: a test that fails on a")
        print("   correct processor is telling you about itself, not about core/.")
    elif orig.ran == 0 or fixed.ran == 0:
        V.no_tests_ran_verdict(orig if orig.ran == 0 else fixed)
    elif not caught:
        print(" VERDICT: FAIL -- row 2. Your testbench cannot tell the dealt core")
        print("   from a correct one, so it is not testing whatever is wrong with it.")
        print("   This is the row that matters and it is the one still open.")
        print("   `make hunt` is the loop; widen the stimulus and run it again.")
    else:
        print(" VERDICT: FAIL -- row 3. You have a test that catches the bug, which")
        print("   is the hard half and it is done. core/ is still broken: fix the")
        print("   line in core/simproc_system.sv and run this again.")
    print(RULE)
    return 1


def reveal():
    name = unseal()
    if name is None:
        print("There is no core/ yet. Run `make new` first.")
        return 1
    print(RULE)
    print(" GIVING UP")
    print(RULE)
    print(f" The core in core/ is {name}.")
    print(f" It hides behind: {BUGS[name]['hides_behind']}")
    print(f" It teaches: {TEACHES[name]}")
    print("")
    print(" You are still not told the line. Now that you know what it is, go")
    print(" and write the test that catches it -- that is the deliverable, and")
    print(" `make verdict` still wants row 2 green. Knowing the name of a bug")
    print(" and owning a test that catches it are different things, and only")
    print(" one of them survives you leaving the project.")
    print(RULE)
    return 0


if __name__ == "__main__":
    args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    mode = sys.argv[1] if sys.argv[1:] and "=" not in sys.argv[1] else "hunt"
    tb = args.get("TB", "test_lab05")
    sim = args.get("SIM", "icarus")
    # VERBOSE= is empty when the Makefile passes it through unset, so anything
    # that is not empty and not a literal 0/no/false turns streaming on.
    verbose = args.get("VERBOSE", "").strip().lower() not in ("", "0", "no", "false")
    if mode == "new":
        deal(args.get("BUG"))
        sys.exit(0)
    if mode == "reveal":
        sys.exit(reveal())
    if mode == "probe":
        sys.exit(hunt(tb, sim, verbose=True))
    if mode == "verdict":
        sys.exit(verdict(tb, sim, verbose=verbose))
    sys.exit(hunt(tb, sim, verbose=verbose))
