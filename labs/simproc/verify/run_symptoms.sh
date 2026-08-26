#!/usr/bin/env bash
# Run verify/test_symptoms.py on the clean core and on every variant, and print
# the lines side by side.  Every number quoted in a variants/*/README.md comes
# from this.  Run inside the workbench container.
#
#   ./verify/run_symptoms.sh /scratch/sym
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
WORK="${1:-/scratch/sym}"
mkdir -p "$WORK"
for V in golden $(cd "$ROOT/variants" && ls -d bug-* ); do
    D="$WORK/$V"
    rm -rf "$D"
    "$ROOT/apply.sh" --force "$V" "$D" >/dev/null
    mkdir -p "$D/verify"
    cp "$HERE"/{simproc.py,golden.py,test_suite.py,test_symptoms.py,test_alu.py,Makefile,Makefile.alu} "$D/verify/"
    echo "===== $V ====="
    ( cd "$D/verify" && make -B COCOTB_TEST_MODULES=test_symptoms \
        SIM_BUILD=sim_build/sym COCOTB_RESULTS_FILE=r_sym.xml 2>&1 ) \
      | grep -E "SYMPTOM|TESTS=" | sed -e 's/^.*SYMPTOM/  SYMPTOM/' -e 's/^.*TESTS=/  TESTS=/'
done
