#!/usr/bin/env python3
"""Count Verilator coverage points that belong to the DESIGN, not the testbench.

`verilator_coverage` prints one merged percentage over everything it compiled,
testbench included, which is not the number you want.  This walks the raw
`.dat` and reports, per file: how many toggle points exist, how many never
fired, and how many LINE points exist.

Usage:  python3 covcount.py cov_six.dat
"""
import os
import re
import sys

DESIGN = ("ripple4.sv", "ripple4_dropped_carry.sv", "fulladder.sv")


def in_design(fields):
    """Match on the basename — Verilator records whatever path it was given."""
    return os.path.basename(fields.get("f", "")) in DESIGN


def read(path):
    pts = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            if not raw.startswith("C "):
                continue
            m = re.match(r"C '(.*)' (\d+)\s*$", raw.rstrip("\n"))
            key, count = m.group(1), int(m.group(2))
            fields = dict(re.findall("\x01(.)\x02([^\x01']*)", key))
            pts.append((fields, count))
    return pts


def main(path):
    pts = read(path)
    toggle = [(f, c) for f, c in pts if f.get("t") == "toggle" and in_design(f)]
    line = [(f, c) for f, c in pts if f.get("t") == "line" and in_design(f)]
    cold = [(f, c) for f, c in toggle if c == 0]

    print(f"{path}")
    print(f"  design toggle points : {len(toggle)}")
    print(f"  never toggled        : {len(cold)}")
    print(f"  design line points   : {len(line)}")
    if cold:
        print("  the ones that never moved:")
        for f, _ in cold:
            print(f"    {os.path.basename(f.get('f'))}:{f.get('l')}  {f.get('o')}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cov_six.dat")
