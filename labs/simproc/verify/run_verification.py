#!/usr/bin/env python3
"""Verify every shipped variant.  Run this inside the workbench container.

    docker run --rm --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" -v /tmp/scratch:/scratch -w /work \
      hpretl/iic-osic-tools:2026.04 --skip bash -c \
      'python3 /work/courses/dd104/labs/simproc/verify/run_verification.py --work /scratch/v'

For each of golden + bug-01..bug-13 it builds a working copy with apply.sh and
answers three questions, none of them by reading the source:

  (a) does it still compile?            -- Icarus builds the chip's own testbench
  (b) does the shipped test still pass? -- test/test.py, the TinyTapeout
                                           boilerplate, exactly as it came.
                                           A bug that fails this is not hidden
                                           and must not ship.
  (c) does a real test catch it?        -- the 10-test systematic suite at the
                                           lab default clk_per_bit = 32, the
                                           same suite at clk_per_bit = 8, and
                                           the baud sweep.

Writes verify/results.json and prints the table.  --quick skips the baud sweep.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from bugs import BUGS, ORDER                                  # noqa: E402

HARNESS = ["simproc.py", "golden.py", "test_suite.py", "test_baud.py",
           "test_symptoms.py", "test_alu.py", "Makefile", "Makefile.alu"]
SUMMARY = re.compile(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+) SKIP=(\d+)")
PERTEST = re.compile(r"\*\* (\w[\w.]*)\s+(PASS|FAIL|SKIP)\s")


def sh(cmd, cwd, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=cwd, env=e, shell=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def scrape(out):
    """(status, {test: PASS/FAIL}) from a cocotb run's output."""
    m = SUMMARY.search(out)
    if not m:
        return "BUILD-FAIL", {}
    tests, npass, nfail, nskip = (int(x) for x in m.groups())
    per = {n.split(".")[-1]: s for n, s in PERTEST.findall(out)
           if not n.startswith("TESTS")}
    return f"{npass}/{tests}", per


def one(variant, work, quick, alu=False):
    d = os.path.join(work, variant)
    shutil.rmtree(d, ignore_errors=True)
    rc, out = sh(f"{ROOT}/apply.sh --force {variant} {d}", ROOT)
    if rc:
        return dict(variant=variant, error=out.strip())
    os.makedirs(os.path.join(d, "verify"), exist_ok=True)
    for f in HARNESS:
        shutil.copy(os.path.join(HERE, f), os.path.join(d, "verify", f))

    res = dict(variant=variant, cat=BUGS.get(variant, {}).get("cat", "-"))

    # (a) + (b): the chip's own testbench, exactly as shipped.
    t0 = time.time()
    rc, out = sh("make -B", os.path.join(d, "test"))
    res["boilerplate"], _ = scrape(out)
    res["compiles"] = "error:" not in out.lower() or res["boilerplate"] != "BUILD-FAIL"
    res["t_boiler"] = round(time.time() - t0, 1)

    # (c): the systematic suite, at the lab default and at the rig's old setting.
    for uio, tag in ((8, "suite32"), (2, "suite8")):
        rc, out = sh(f"make -B COCOTB_TEST_MODULES=test_suite "
                     f"SIM_BUILD=sim_build/{tag} COCOTB_RESULTS_FILE=r_{tag}.xml",
                     os.path.join(d, "verify"), env={"SIMPROC_UIO": str(uio)})
        st, per = scrape(out)
        res[tag] = st
        res[tag + "_fail"] = sorted(k.split("_")[0] for k, v in per.items() if v == "FAIL")

    if alu:
        rc, out = sh("make -f Makefile.alu -B", os.path.join(d, "verify"))
        res["alu"], _ = scrape(out)
        res["alu_detail"] = [l.split("ALU ", 1)[-1].strip()
                             for l in out.splitlines() if " ALU " in l]

    if not quick:
        rc, out = sh("make -B COCOTB_TEST_MODULES=test_baud "
                     "SIM_BUILD=sim_build/baud COCOTB_RESULTS_FILE=r_baud.xml",
                     os.path.join(d, "verify"))
        res["baud"], _ = scrape(out)
        res["baud_detail"] = [l.strip() for l in out.splitlines()
                              if re.search(r"clk_per_bit=\d", l)]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/scratch/v")
    ap.add_argument("--quick", action="store_true", help="skip the baud sweep")
    ap.add_argument("--only", default=None, help="comma-separated variant ids")
    ap.add_argument("--alu", action="store_true",
                    help="also run the 393,216-vector ALU sweep (~19 s a variant)")
    a = ap.parse_args()

    names = a.only.split(",") if a.only else ["golden"] + ORDER
    os.makedirs(a.work, exist_ok=True)
    rows = []
    for n in names:
        t0 = time.time()
        r = one(n, a.work, a.quick, a.alu)
        r["seconds"] = round(time.time() - t0, 1)
        rows.append(r)
        print(f"[{len(rows)}/{len(names)}] {n:8s} "
              f"boilerplate={r.get('boilerplate'):9s} "
              f"suite@cpb32={r.get('suite32'):7s} suite@cpb8={r.get('suite8'):7s} "
              f"baud={r.get('baud', '-'):5s} alu={r.get('alu', '-'):5s} "
              f"({r['seconds']}s)", flush=True)

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(rows, f, indent=1)

    print("\n" + "=" * 100)
    print(f"{'variant':9s} {'cat':4s} {'boiler':7s} {'cpb=32':7s} {'cpb=8':7s} "
          f"{'baud':6s}  caught by (at the lab default, clk_per_bit = 32)")
    print("=" * 100)
    bad = []
    for r in rows:
        caught = ",".join(r.get("suite32_fail", [])) or "-"
        if r["variant"] != "golden" and r.get("baud", "1/1") != "1/1":
            caught += " +BAUD"
        if r["variant"] != "golden" and r.get("alu", "1/1") != "1/1":
            caught += " +ALU"
        print(f"{r['variant']:9s} {r.get('cat','-'):4s} {r.get('boilerplate','?'):7s} "
              f"{r.get('suite32','?'):7s} {r.get('suite8','?'):7s} "
              f"{r.get('baud','-'):6s}  {caught}")
        if r["variant"] == "golden":
            if r.get("suite32") != "10/10" or r.get("suite8") != "10/10" \
                    or r.get("alu", "1/1") != "1/1" or r.get("baud", "1/1") != "1/1":
                bad.append(f"{r['variant']}: the CORRECT core does not pass its own tests")
            continue
        if r.get("boilerplate") != "1/1":
            bad.append(f"{r['variant']}: fails the shipped boilerplate test -- not hidden, do not ship")
        if caught == "-":
            bad.append(f"{r['variant']}: nothing catches it -- do not ship")
    print("=" * 100)
    for b in bad:
        print("  DROP:", b)
    print(f"\n{len(rows)} variants checked, {len(bad)} problem(s).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
