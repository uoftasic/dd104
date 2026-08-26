"""
DD104 Lab 05 — the first command of this lab, and it proves a negative.

    make blind

Runs `test_architecture.py` -- an architecturally complete testbench, the kind
of thing your Lab 04 suite grew into -- against the golden core and against
both of the cores in this lab's pool.

All three columns come back green.  That is the lab.  Both of those cores are
genuinely broken and every register, every flag, every byte of memory and every
PC value they produce is correct, so a testbench that looks at architectural
state cannot tell them apart from a working processor no matter how thorough it
is.  Thoroughness is not the missing ingredient.  A different KIND of check is.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.abspath(os.path.join(HERE, "..", "common"))
sys.path.insert(0, COMMON)
sys.path.insert(0, HERE)

import inject                                   # noqa: E402
import verdict as V                             # noqa: E402
from hunt import run_sim, row, RULE, THIN       # noqa: E402

POOL = ["B08", "B13"]
TB = "test_architecture"


def main():
    good = run_sim(TB, os.path.join(COMMON, "rtl"),
                   os.path.join(HERE, "build", "blind-golden"))
    print(row(good.mark("pass"), "the golden core", good))
    if not good.launched:
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        return 1

    # This demonstration only means anything if the testbench actually runs.
    # A test that blew up would print three identical rows too, and they would
    # be three crashes rather than three green passes -- the opposite lesson,
    # told in the same shape.
    if not good.all_passed:
        print(THIN)
        V.report_problems(good)
        if good.broken:
            V.broken_testbench_verdict(good, "the golden core")
        elif good.ran == 0:
            V.no_tests_ran_verdict(good)
        else:
            print(" Stopping: test_architecture.py does not pass the golden core,")
            print(" so 'it passes on the broken ones too' is not a thing this run")
            print(" can show you.")
        print(RULE)
        return 1

    blew_up = []
    for b in POOL:
        rtl = inject.build(b, os.path.join(HERE, "build", "blind", b))
        r = run_sim(TB, rtl, os.path.join(HERE, "build", "blind", b, "run"))
        if r.broken:
            blew_up.append((b, r))
        print(row(r.mark("fail"), b, r))

    if blew_up:
        print(THIN)
        for b, r in blew_up:
            V.report_problems(r)
        V.broken_testbench_verdict(blew_up[0][1], blew_up[0][0])
        print(RULE)
        return 1

    print(THIN)
    print(" Three identical green rows. Every architectural result on all three")
    print(" of those processors is correct, and two of them are broken.")
    print("")
    print(" What test_architecture.py never reads: the `done` pin, the `halt`")
    print(" pin, and the number of clock cycles anything took. Those are the")
    print(" three things this lab is about.")
    print(RULE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
