"""
DD104 — the bug hunt.

    make new        deal a mystery core.  You are not told which bug it is.
    make hunt       your testbench against that core -- the loop you live in
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
────────────────────────────────────────────────────────────────────────────
"""

import base64
import os
import random
import shutil
import subprocess
import textwrap
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


def run_sim(tb, rtl_dir, build_dir, sim="icarus"):
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


def hunt(tb, sim="icarus"):
    """Run the testbench against core/ and print what happened.  No grade."""
    if not os.path.exists(CORE):
        print("There is no core/ yet. Run `make new` first.")
        return 1
    name = unseal()
    print(RULE)
    print(f" HUNT   testbench: {tb}   target: core/")
    print(RULE)
    r = run_sim(tb, CORE, os.path.join(HERE, "build", "hunt"), sim=sim)
    print(row("caught" if r.failures else "quiet", "core/  the mystery", r))
    for tname, msg in r.failures[:6]:
        print(f"        {tname}")
        print(f"            {msg[:100]}")
    print(THIN)
    if not r.launched:
        print(" The simulator never produced a results file. That is a setup problem,")
        print(" not a test failure. The last 20 lines of its output:")
        for l in r.log.strip().splitlines()[-20:]:
            print("   " + l)
        return 1
    if r.failures:
        print(" Something in this core disagrees with your testbench. That is not")
        print(" yet a verdict -- your test could be wrong. `make verdict` runs it")
        print(" against the golden core too, which is what settles it.")
    else:
        print(" Nothing your testbench drives can tell this core from a correct")
        print(" one. The bug is real and it is in there; your stimulus has not")
        print(" reached it yet. Widen the stimulus, not the assertions.")
    print(RULE)
    return 0


def verdict(tb, sim="icarus"):
    name = unseal()
    if not os.path.exists(CORE) or name is None:
        print("There is no core/ yet. Run `make new` first.")
        return 1

    print(RULE)
    print(f" VERDICT   testbench: {tb}   simulator: {sim}")
    print(RULE)

    good = run_sim(tb, os.path.join(COMMON, "rtl"),
                   os.path.join(HERE, "build", "golden"), sim=sim)
    print(row("ok" if good.all_passed else "FAIL",
              "1. the golden core          must PASS", good))
    if not good.launched:
        print(THIN)
        print(" The simulator never produced a results file. That is a setup problem,")
        print(" not a test failure. The last 20 lines of its output:")
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        print(RULE)
        return 1
    for tname, msg in good.failures[:4]:
        print(f"        {tname}\n            {msg[:100]}")

    # Row 2 is rebuilt from the catalogue, never read from core/.
    fresh = inject.build(name, os.path.join(HERE, "build", "original"))
    orig = run_sim(tb, fresh, os.path.join(HERE, "build", "original", "run"), sim=sim)
    caught = orig.launched and orig.tests > 0 and bool(orig.failures)
    print(row("caught" if caught else "MISSED",
              "2. the core you were dealt  must FAIL", orig))
    for tname, msg in orig.failures[:4]:
        print(f"        {tname}\n            {msg[:100]}")

    fixed = run_sim(tb, CORE, os.path.join(HERE, "build", "fixed"), sim=sim)
    print(row("ok" if fixed.all_passed else "FAIL",
              "3. core/ as it stands now   must PASS", fixed))
    for tname, msg in fixed.failures[:4]:
        print(f"        {tname}\n            {msg[:100]}")

    print(THIN)
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
    if mode == "new":
        deal(args.get("BUG"))
        sys.exit(0)
    if mode == "reveal":
        sys.exit(reveal())
    if mode == "verdict":
        sys.exit(verdict(tb, sim))
    sys.exit(hunt(tb, sim))
