#!/usr/bin/env bash
# apply.sh -- build a working copy of the SimProc core, with one bug in it.
#
#   ./apply.sh bug-07 /tmp/lab2-core     one buggy core, ready to simulate
#   ./apply.sh golden /tmp/clean-core    the correct core (reference / instructor)
#
# The result is a self-contained package:
#
#   <destdir>/src/       the two RTL files -- this is what the student edits
#   <destdir>/test/      the testbench that shipped with the chip, untouched
#   <destdir>/README.md  what the student is told: the symptom, and nothing else
#   <destdir>/VARIANT    the variant id, so a bug report can name which core it was
#
# What it deliberately does NOT copy: golden/, the .patch, solutions/, verify/.
# A package built by this script can be handed to a student as-is.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=0

usage() {
    echo "usage: $0 [--force] <variant> <destdir>"
    echo
    echo "variants:"
    echo "  golden          the correct core"
    for d in "$HERE"/variants/bug-*/; do
        [ -d "$d" ] || continue
        echo "  $(basename "$d")"
    done
    exit 2
}

while [ $# -gt 0 ]; do
    case "$1" in
        --force) FORCE=1; shift ;;
        -h|--help) usage ;;
        -*) echo "apply.sh: unknown option $1" >&2; usage ;;
        *) break ;;
    esac
done

[ $# -eq 2 ] || usage
VARIANT="$1"
DEST="$2"

if [ "$VARIANT" != "golden" ] && [ ! -f "$HERE/variants/$VARIANT/bug.patch" ]; then
    echo "apply.sh: no such variant '$VARIANT'" >&2
    usage
fi

if [ -e "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ] && [ "$FORCE" -eq 0 ]; then
    echo "apply.sh: $DEST is not empty (use --force to overwrite)" >&2
    exit 1
fi

mkdir -p "$DEST/src" "$DEST/test"
cp "$HERE"/golden/src/*.sv          "$DEST/src/"
cp "$HERE"/golden/test/tb.v         "$DEST/test/"
cp "$HERE"/golden/test/test.py      "$DEST/test/"
cp "$HERE"/golden/test/Makefile     "$DEST/test/"
cp "$HERE"/golden/test/requirements.txt "$DEST/test/"
echo "$VARIANT" > "$DEST/VARIANT"

if [ "$VARIANT" = "golden" ]; then
    cp "$HERE/golden/README.md" "$DEST/README.md"
    echo "apply.sh: wrote the CORRECT core to $DEST  (reference copy -- not a lab package)"
    exit 0
fi

# `patch` ships in the workbench image; git is the fallback for a bare host.
if command -v patch >/dev/null 2>&1; then
    ( cd "$DEST" && patch -p1 --silent < "$HERE/variants/$VARIANT/bug.patch" )
elif command -v git >/dev/null 2>&1; then
    ( cd "$DEST" && git apply --unsafe-paths --directory=. "$HERE/variants/$VARIANT/bug.patch" )
else
    echo "apply.sh: need either 'patch' or 'git' to apply the variant" >&2
    exit 1
fi

cp "$HERE/variants/$VARIANT/README.md" "$DEST/README.md"
echo "apply.sh: wrote $VARIANT to $DEST"
