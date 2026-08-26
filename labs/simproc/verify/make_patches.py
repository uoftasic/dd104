#!/usr/bin/env python3
"""Regenerate variants/bug-NN/bug.patch from golden/ + verify/bugs.py.

    python3 verify/make_patches.py            # write the patches
    python3 verify/make_patches.py --check    # fail if any patch is stale

Every patch is a unified diff against `golden/src/simproc_system.sv`, applied
from the root of a working copy with `patch -p1` (that is what apply.sh does).
"""
import difflib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from bugs import BUGS, ORDER, apply_edits          # noqa: E402

GOLDEN = os.path.join(ROOT, "golden", "src", "simproc_system.sv")
REL = "src/simproc_system.sv"


def patch_text(name, golden):
    bugged = apply_edits(golden, name)
    diff = difflib.unified_diff(
        golden.splitlines(keepends=True), bugged.splitlines(keepends=True),
        fromfile="a/" + REL, tofile="b/" + REL, n=3)
    return "".join(diff)


def main():
    check = "--check" in sys.argv
    golden = open(GOLDEN).read()
    stale = []
    for name in ORDER:
        p = patch_text(name, golden)
        assert p, f"{name}: empty patch"
        d = os.path.join(ROOT, "variants", name)
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, "bug.patch")
        if check:
            cur = open(f).read() if os.path.exists(f) else None
            if cur != p:
                stale.append(name)
        else:
            open(f, "w").write(p)
            print(f"{name}  {BUGS[name]['cat']}  {len(p.splitlines())} diff lines"
                  f"  -- {BUGS[name]['title']}")
    if check:
        if stale:
            print("STALE:", " ".join(stale))
            return 1
        print(f"all {len(ORDER)} patches match golden/ + bugs.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
