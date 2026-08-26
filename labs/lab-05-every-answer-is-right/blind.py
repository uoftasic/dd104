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
from hunt import run_sim, row, RULE, THIN       # noqa: E402

POOL = ["B08", "B13"]
TB = "test_architecture"


def main():
    good = run_sim(TB, os.path.join(COMMON, "rtl"),
                   os.path.join(HERE, "build", "blind-golden"))
    print(row("ok" if good.all_passed else "FAIL", "the golden core", good))
    if not good.launched:
        for l in good.log.strip().splitlines()[-20:]:
            print("   " + l)
        return 1

    for b in POOL:
        rtl = inject.build(b, os.path.join(HERE, "build", "blind", b))
        r = run_sim(TB, rtl, os.path.join(HERE, "build", "blind", b, "run"))
        print(row("MISSED" if r.all_passed else "caught", b, r))

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
