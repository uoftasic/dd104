"""
DD104 — build a deliberately broken SimProc.

    python3 inject.py B01              # writes build/B01_.../rtl/
    python3 inject.py --list           # what is in the catalogue
    python3 inject.py --verify         # check every anchor still matches

`check.py` calls this for you.  You will rarely run it by hand — but it is
short, and reading it tells you exactly how much a "bug" is: one line.

The important part is the assertion.  Before changing anything, the injector
checks that the line it is about to replace still contains the exact text the
catalogue expects.  If somebody edits `rtl/simproc_system.sv` and the line
numbers move, this **fails** rather than silently patching the wrong line and
handing you a "broken" core that is actually fine.  A grader that says PASS
when it did nothing is worse than no grader at all.
"""

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bugs import BUGS, names, resolve      # noqa: E402

GOLDEN_RTL = os.path.join(HERE, "rtl")
DEFAULT_BUILD = os.path.join(HERE, "build")

# Everything in rtl/ that a simulation needs, copied verbatim into the variant.
RTL_FILES = ["simproc_system.sv", "tt_um_ieeeuoftasic_simproc.sv", "tb.v"]


def build(name, out_dir=None):
    """Write a copy of the RTL with one bug in it.  Returns the directory."""
    name = resolve(name)
    out_dir = out_dir or os.path.join(DEFAULT_BUILD, name)
    rtl_out = os.path.join(out_dir, "rtl")
    os.makedirs(rtl_out, exist_ok=True)

    for f in RTL_FILES:
        shutil.copy(os.path.join(GOLDEN_RTL, f), os.path.join(rtl_out, f))

    path = os.path.join(rtl_out, "simproc_system.sv")
    lines = open(path).read().split("\n")
    for lineno, expected, replacement in BUGS[name]["edits"]:
        actual = lines[lineno - 1]
        if actual != expected:
            raise AssertionError(
                f"\n{name}: rtl/simproc_system.sv line {lineno} has drifted.\n"
                f"  the catalogue expects: {expected!r}\n"
                f"  the file actually has: {actual!r}\n"
                f"Refusing to inject — patching the wrong line would produce a "
                f"'broken' core that is not broken, and every check against it "
                f"would be meaningless.")
        lines[lineno - 1] = replacement
    open(path, "w").write("\n".join(lines))
    return rtl_out


def verify_all():
    """Check every anchor in the catalogue against the shipped RTL."""
    src = open(os.path.join(GOLDEN_RTL, "simproc_system.sv")).read().split("\n")
    bad = []
    for name in names():
        for lineno, expected, _ in BUGS[name]["edits"]:
            if src[lineno - 1] != expected:
                bad.append((name, lineno, expected, src[lineno - 1]))
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("bug", nargs="?", help="catalogue name, or a prefix like B01")
    ap.add_argument("-o", "--out", help="where to write the variant")
    ap.add_argument("--list", action="store_true", help="list the catalogue")
    ap.add_argument("--verify", action="store_true",
                    help="check every anchor against rtl/ and exit")
    args = ap.parse_args()

    if args.list:
        for n in names():
            print(f"  tier {BUGS[n]['tier']}   {n}")
        sys.exit(0)

    if args.verify:
        bad = verify_all()
        if not bad:
            print(f"all {len(BUGS)} catalogue anchors match rtl/simproc_system.sv")
            sys.exit(0)
        for name, lineno, want, got in bad:
            print(f"{name}: line {lineno}\n  want {want!r}\n  got  {got!r}")
        sys.exit(1)

    if not args.bug:
        ap.error("name a bug, or pass --list / --verify")
    out = build(args.bug, args.out)
    print(f"injected {resolve(args.bug)} -> {out}")
