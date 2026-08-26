"""
DD104 — does the grader actually grade?

    cd labs/common && make selftest          the fast half, no simulator
    cd labs/common && make selftest FULL=1   ... and every checker, for real

`inject.py` says it, and it is the reason this file exists:

    A grader that says PASS when it did nothing is worse than no grader at all.

DD104 shipped two of those.  A testbench whose failure path raised NameError
was counted as having *caught* three ALU bugs, because the harness could not
tell "the assertion fired" from "the test blew up".  And a student who did
half of Lab 01's TODO got `VERDICT: PASS ... That is a test worth committing`.

So the checkers are themselves tested, by pointing them at testbenches that
are known-bad in a specific way and reading what they say.  Every fixture in
this directory is deliberately broken, every one names the verdict it must
provoke in its own docstring, and this script fails loudly if the verdict has
drifted.

────────────────────────────────────────────────────────────────────────────
PART 1 -- the classifier, with no simulator involved
────────────────────────────────────────────────────────────────────────────
Hand-written results.xml files, one per shape cocotb 2.0.1 can produce, run
through `verdict.py`. Sub-second, and it is the part that catches a
regression in the rule itself.

────────────────────────────────────────────────────────────────────────────
PART 2 -- the shipped checkers, end to end   (FULL=1)
────────────────────────────────────────────────────────────────────────────
Every `check*.py` and `hunt.py` in the course, each fed a broken testbench,
each required to print a specific verdict. Minutes, not seconds -- one of
these runs the whole 393,216-vector ALU sweep three times.

A lab with a hunt in progress (a `core/` directory) is SKIPPED rather than
dealt over: `make new` deletes core/, and this script will not do that to you.
"""

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.abspath(os.path.join(HERE, ".."))
LABS = os.path.abspath(os.path.join(COMMON, ".."))
sys.path.insert(0, COMMON)

import verdict as V                              # noqa: E402

RULE = "=" * 72
THIN = "-" * 72

LAB01 = os.path.join(LABS, "lab-01-the-adder-you-already-trust")
LAB03 = os.path.join(LABS, "lab-03-three-blocks-before-the-processor")


# ─────────────────────────────────────────────────────────────────────────────
# PART 1 — the classifier
# ─────────────────────────────────────────────────────────────────────────────

CASE = ('  <testcase name="{name}" classname="t" sim_time_ns="{ns}">{body}'
        '</testcase>')


def xml(*cases):
    body = "\n".join(CASE.format(**c) for c in cases)
    return f'<testsuites name="results">\n <testsuite name="all">\n{body}\n'\
           f' </testsuite>\n</testsuites>\n'


def case(name, body="", ns="1.0"):
    return dict(name=name, body=body, ns=ns)


FAIL = '<failure error_type="AssertionError" error_msg="2 of 4 wrong" />'
CRASH = '<failure error_type="NameError" error_msg="name \'x\' is not defined" />'
TYPO = '<failure error_type="TypeError" error_msg="unsupported operand" />'
INIT = '<failure msg="Test initialization failed" />'
TMOUT = '<failure error_type="TimeoutError" error_msg="never reached the park" />'
SKIP = "<skipped />"

# (label, cases, all_passed, caught, broken, ran)
CLASSIFIER_CASES = [
    ("every test passed",
     [case("a"), case("b")], True, False, False, 2),

    ("one assertion fired -- a real catch",
     [case("a"), case("b", FAIL)], False, True, False, 2),

    ("one test raised NameError -- NOT a catch",
     [case("a"), case("b", CRASH)], False, False, True, 2),

    ("one test raised TypeError -- NOT a catch",
     [case("a"), case("b", TYPO)], False, False, True, 2),

    ("an assertion fired AND another test crashed -- still not a verdict",
     [case("a", FAIL), case("b", CRASH)], False, False, True, 2),

    ("the test could not be initialised (no error_type) -- NOT a catch",
     [case("a", INIT)], False, False, True, 1),

    ("a timeout in simproc.run() -- IS a catch, no assert involved",
     [case("a", TMOUT)], False, True, False, 1),

    ("every test skipped -- NOT 'all passed'",
     [case("a", SKIP), case("b", SKIP)], False, False, False, 0),

    ("one skipped, one passed -- passing, but the count is honest",
     [case("a", SKIP), case("b")], True, False, False, 1),
]


def part1():
    print(RULE)
    print(" PART 1   the classifier, against hand-written results.xml")
    print(RULE)
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "results.xml")
        for label, cases, want_pass, want_caught, want_broken, want_ran in CLASSIFIER_CASES:
            open(p, "w").write(xml(*cases))
            r = V.read_results(p)
            got = (r.all_passed, r.caught, r.broken, r.ran)
            want = (want_pass, want_caught, want_broken, want_ran)
            ok = got == want
            bad += not ok
            print(f"  {'ok' if ok else 'WRONG':>6}  {label}")
            print(f"          -> {r.summary()}   "
                  f"all_passed={r.all_passed} caught={r.caught} broken={r.broken}")
            if not ok:
                print(f"          EXPECTED all_passed/caught/broken/ran = {want}, got {got}")
    print(THIN)
    print(f" {len(CLASSIFIER_CASES) - bad} of {len(CLASSIFIER_CASES)} classifier cases correct.")
    print(RULE)
    return bad == 0


# ─────────────────────────────────────────────────────────────────────────────
# PART 2 — the shipped checkers, end to end
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd, cwd):
    """Run a checker with this directory on PYTHONPATH so the fixtures import.

    sim.mk appends the inherited PYTHONPATH to its own, so setting it here is
    enough to make `TB=tb_adder_empty` resolve from selftest/."""
    env = dict(os.environ)
    env["PYTHONPATH"] = HERE + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


class Expect:
    """One end-to-end case: run a checker, then read what it said."""

    def __init__(self, label, cmd, cwd, must_say, must_not_say=("VERDICT: PASS",),
                 must_exit_nonzero=True):
        self.label = label
        self.cmd = cmd
        self.cwd = cwd
        self.must_say = must_say
        self.must_not_say = must_not_say
        self.must_exit_nonzero = must_exit_nonzero

    def check(self):
        code, out = run(self.cmd, self.cwd)
        problems = []
        for s in self.must_say:
            if s not in out:
                problems.append(f'did not say "{s}"')
        for s in self.must_not_say:
            if s in out:
                problems.append(f'said "{s}" and must not')
        if self.must_exit_nonzero and code == 0:
            problems.append("exited 0")
        return problems, out


def cases_fast():
    py = sys.executable
    return [
        Expect("lab-01  a testbench that crashes on every core",
               [py, os.path.join(LAB01, "check.py"), "tb_adder_blows_up"], LAB01,
               must_say=["BLEW UP", "NameError", "VERDICT: FAIL"]),

        Expect("lab-01  a testbench that crashes only when the design is wrong",
               [py, os.path.join(LAB01, "check.py"), "tb_adder_blows_up_on_failure"], LAB01,
               must_say=["BLEW UP", "NameError", "VERDICT: FAIL",
                         "did not run to the end"]),

        Expect("lab-01  the lazy testbench",
               [py, os.path.join(LAB01, "check.py"), "tb_adder_empty"], LAB01,
               must_say=["MISSED", "passes the broken adder too"]),

        Expect("lab-01  half the TODO: swept cin, still asserts on the first bad vector",
               [py, os.path.join(LAB01, "check.py"), "tb_adder_half_todo"], LAB01,
               must_say=["second half of the TODO is not done",
                         "stopped", "VERDICT: FAIL"]),

        Expect("lab-01  the shipped file, untouched",
               [py, os.path.join(LAB01, "check.py"), "test_adder"], LAB01,
               must_say=["MISSED", "passes the broken adder too"]),

        Expect("lab-01  the reference solution",
               [py, os.path.join(LAB01, "check.py"), "test_solution_selftest"], LAB01,
               must_say=["VERDICT: PASS", "512 vectors"],
               must_not_say=("VERDICT: FAIL", "BLEW UP"),
               must_exit_nonzero=False),
    ]


def cases_slow():
    py = sys.executable
    return [
        Expect("lab-03  crash in the failure path, one bug",
               [py, os.path.join(LAB03, "check.py"), "one",
                "TB=tb_alu_blows_up_on_failure", "TOPLEVEL=ALU", "BUG=B01"], LAB03,
               must_say=["BROKEN", "NameError", "VERDICT: FAIL"]),

        Expect("lab-03  crash in the failure path, the three-bug sweep",
               [py, os.path.join(LAB03, "check.py"), "sweep",
                "TB=tb_alu_blows_up_on_failure", "TOPLEVEL=ALU"], LAB03,
               must_say=["NO COUNT", "NameError"],
               must_not_say=("VERDICT: PASS", "3 of 3 ALU bugs caught")),

        Expect("common  crash in the failure path, one bug",
               [py, os.path.join(COMMON, "check.py"), "--tb",
                "tb_core_blows_up_on_failure", "--bug", "B01",
                "--dir", COMMON], COMMON,
               must_say=["BROKEN", "NameError", "VERDICT: FAIL"]),

        Expect("common  the lazy testbench, one bug",
               [py, os.path.join(COMMON, "check.py"), "--tb", "tb_core_empty",
                "--bug", "B01", "--dir", COMMON], COMMON,
               must_say=["MISSED", "passes"]),
    ]


# Which bug to deal into each hunt lab, and which fixture reaches it.
#
# The fixture has to be able to SEE the bug before it can crash on it. Lab 05's
# pool changes no register, flag or byte of memory -- that is the whole lab --
# so the register-comparing fixture is MISSED there rather than BROKEN, and the
# handshake one is the only thing that gets far enough to crash. Getting this
# pairing wrong makes the selftest fail for a reason that is not a bug in the
# checker, so it is written down here rather than guessed.
HUNT_LABS = [
    ("lab-04-your-first-bug-hunt",   "B04", "tb_core_blows_up_on_failure"),
    ("lab-05-every-answer-is-right", "B08", "tb_core_handshake_blows_up"),
    ("lab-06-capstone",              "B11", "tb_core_blows_up_on_failure"),
]


def hunt_cases():
    """lab-04, lab-05 and lab-06 -- only where no hunt is in progress."""
    py = sys.executable
    out = []
    for lab, bug, tb in HUNT_LABS:
        d = os.path.join(LABS, lab)
        if os.path.exists(os.path.join(d, "core")):
            print(f"  {'SKIP':>6}  {lab}: core/ exists, and `make new` would")
            print("          delete it. Finish or `make clean` that hunt first.")
            continue
        out.append((d, bug, lab, py, tb))
    return out


def part2(full):
    print(RULE)
    print(" PART 2   the shipped checkers, end to end")
    print(RULE)
    if not full:
        print(" Skipped. This part starts simulators and takes minutes.")
        print("     make selftest FULL=1")
        print(RULE)
        return True

    # The reference solution under a name check.py can import.
    src = os.path.join(LAB01, "solutions", "test_adder.py")
    dst = os.path.join(LAB01, "test_solution_selftest.py")
    open(dst, "w").write(open(src).read())

    bad = 0
    try:
        for e in cases_fast() + cases_slow():
            problems, out = e.check()
            bad += bool(problems)
            print(f"  {'ok' if not problems else 'WRONG':>6}  {e.label}")
            for p in problems:
                print(f"          {p}")
            if problems:
                print(THIN)
                for l in out.strip().splitlines()[-25:]:
                    print("          " + l)
                print(THIN)
    finally:
        os.path.exists(dst) and os.remove(dst)

    for d, bug, lab, py, tb in hunt_cases():
        import shutil
        try:
            run([py, os.path.join(d, "hunt.py"), "new", f"BUG={bug}"], d)
            e = Expect(f"{lab}  crash in the failure path, the three-row grade",
                       [py, os.path.join(d, "hunt.py"), "verdict", f"TB={tb}"], d,
                       must_say=["BROKEN", "NameError", "VERDICT: FAIL"])
            problems, out = e.check()
            bad += bool(problems)
            print(f"  {'ok' if not problems else 'WRONG':>6}  {e.label}")
            for p in problems:
                print(f"          {p}")
            if problems:
                print(THIN)
                for l in out.strip().splitlines()[-25:]:
                    print("          " + l)
                print(THIN)
        finally:
            shutil.rmtree(os.path.join(d, "core"), ignore_errors=True)

    print(THIN)
    print(" every checker refused every broken testbench." if not bad
          else f" {bad} checker(s) said the wrong thing. That is the serious kind.")
    print(RULE)
    return bad == 0


# ─────────────────────────────────────────────────────────────────────────────
# PART 3 — nobody has re-grown their own copy of the rule
# ─────────────────────────────────────────────────────────────────────────────

CHECKERS = [
    os.path.join(COMMON, "check.py"),
    os.path.join(LAB01, "check.py"),
    os.path.join(LAB03, "check.py"),
    os.path.join(LABS, "lab-04-your-first-bug-hunt", "hunt.py"),
    os.path.join(LABS, "lab-05-every-answer-is-right", "hunt.py"),
    os.path.join(LABS, "lab-06-capstone", "hunt.py"),
]

# The two idioms that were the bug. `findall("error")` never matches anything
# cocotb 2.x writes, and treating every <failure> as a catch is exactly how a
# crash became `caught`.
FORBIDDEN = [
    (re.compile(r'findall\(\s*["\']error["\']\s*\)'),
     'findall("error") -- cocotb 2.x never writes an <error> element'),
    (re.compile(r'^\s*class Result:', re.M),
     "a local copy of Result -- import it from verdict.py instead"),
    (re.compile(r'ET\.parse'),
     "its own results.xml parser -- use verdict.read_results()"),
]


def part3():
    print(RULE)
    print(" PART 3   every checker reads the rule from verdict.py")
    print(RULE)
    bad = 0
    for f in CHECKERS:
        src = open(f).read()
        hits = [why for rx, why in FORBIDDEN if rx.search(src)]
        if "import verdict" not in src:
            hits.append("does not import verdict.py at all")
        bad += bool(hits)
        print(f"  {'ok' if not hits else 'WRONG':>6}  {os.path.relpath(f, LABS)}")
        for h in hits:
            print(f"          {h}")
    print(THIN)
    print(f" {len(CHECKERS) - bad} of {len(CHECKERS)} checkers.")
    print(RULE)
    return bad == 0


# ─────────────────────────────────────────────────────────────────────────────
# PART 4 — the answer key agrees with the catalogue
# ─────────────────────────────────────────────────────────────────────────────
#
# `bugs.py` is what the tooling prints: `make bugs` groups by tier, and every
# `check-all` row is labelled `tier N`.  `labs/simproc/solutions/bug-NN.md` is
# what a student reads when they give up.  When those two disagree the course
# is telling one story to the grader and another to the reader.
#
# They did disagree: six of the thirteen answer files carried a tier that
# `bugs.py` does not, left over from a five-lab plan the course no longer has.
# Nothing executed those numbers, so nothing caught them. This part does.

SOLUTIONS = os.path.join(LABS, "simproc", "solutions")

HEADER = re.compile(r"Catalogue \*\*(B\d\d)\*\*\.\s*Tier (\d)", re.M)

# Which shipped lab each tier is met in. Derived from the tooling, not from
# prose: lab-03/check.py sweeps ALU_BUGS (tier 1), and selftest's own HUNT_LABS
# deals B04 (tier 2) into lab-04, B08 (tier 4) into lab-05, B11 (tier 5) into
# lab-06. Tier 3 is hunted in lab-04 alongside tier 2.
TIER_LAB = {1: "Lab 03", 2: "Lab 04", 3: "Lab 04", 4: "Lab 05", 5: "Lab 06"}


def part4():
    print(RULE)
    print(" PART 4   the answer key agrees with bugs.py")
    print(RULE)
    sys.path.insert(0, COMMON)
    from bugs import BUGS                        # noqa: E402

    by_num = {name[:3]: name for name in BUGS}
    bad = 0
    for i in range(1, len(BUGS) + 1):
        b = f"B{i:02d}"
        f = os.path.join(SOLUTIONS, f"bug-{i:02d}.md")
        if not os.path.exists(f):
            print(f"  {'WRONG':>6}  bug-{i:02d}.md is missing")
            bad += 1
            continue
        m = HEADER.search(open(f).read())
        if not m:
            print(f"  {'WRONG':>6}  bug-{i:02d}.md has no 'Catalogue **BNN**. Tier N' header")
            bad += 1
            continue
        got_bug, got_tier = m.group(1), int(m.group(2))
        want_tier = BUGS[by_num[b]]["tier"]
        hits = []
        if got_bug != b:
            hits.append(f"header says {got_bug}, file is bug-{i:02d}")
        if got_tier != want_tier:
            hits.append(f"says tier {got_tier}, bugs.py says tier {want_tier}")
        # the lab named on the header line must be the one that tier is met in
        line = m.string[m.start():m.string.find("\n", m.start())]
        want_lab = TIER_LAB[want_tier]
        if want_lab not in line:
            hits.append(f"does not name {want_lab}, where tier {want_tier} is met")
        bad += bool(hits)
        print(f"  {'ok' if not hits else 'WRONG':>6}  bug-{i:02d}.md")
        for h in hits:
            print(f"          {h}")
    print(THIN)
    print(f" {len(BUGS) - bad} of {len(BUGS)} answer files match the catalogue.")
    print(RULE)
    return bad == 0


def main():
    full = os.environ.get("FULL", "").strip().lower() not in ("", "0", "no", "false")
    ok = part1()
    ok = part3() and ok
    ok = part4() and ok
    ok = part2(full) and ok
    print("")
    print(" SELFTEST: PASS" if ok else " SELFTEST: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
