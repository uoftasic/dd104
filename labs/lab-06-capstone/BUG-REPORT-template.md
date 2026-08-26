# Bug report — `<bug id>`

Copy this file to `BUG-REPORT.md` and fill it in for one of the three bugs in this lab's pool.

The deliverable of verification is not a red test. It is a report somebody can act on without
re-deriving your week. Five parts, in this order, because that is the order the reader needs
them in.

---

## 1. The smallest program that reproduces it

Minimise. Cut instructions until it stops failing, then put the last one back. A ten-line
repro and a three-line repro are the same bug and very different amounts of work for the
person who has to fix it.

```python
# a complete, runnable program -- the list of instruction bytes, or the
# assemble("""...""") block, exactly as your test drives it
```

How to run it:

```bash
make check TB=<your module> BUG=<bug id>
```

## 2. Expected versus actual, as numbers, with the arithmetic shown

Not "r1 is wrong". The number you expected, the number you got, and the sum that produces the
expected one.

| | |
|---|---|
| expected | |
| actual | |
| why the expected value is what it is | |

## 3. The shape

How many vectors, cases or cycles are wrong, out of how many — and what that count implies
before anybody opens the RTL.

A count is a diagnosis when it factors. `65,024 of 65,536` leaves 512 survivors, and 512 has a
description. `0 value mismatches and 25,726 flag mismatches` says the arithmetic is fine.
`exactly half` says the fault tracks a signal that is high half the time.

## 4. Where it is *not*

What still works. This is the part that makes a report credible, and it is the part that
localises the fix.

- Which instructions are unaffected?
- Which registers, addresses, flags?
- Does it survive a reset? Does it depend on the operands being different?
- Which of your other tests pass on this core, and what does that rule out?

## 5. The reflex the suite gained

One line. The rule a person can carry to the next design, and the test that enforces it here,
by name.

> Reflex: *…*
>
> Enforced by: `<test function name>` in `<file>`, which fails on this core and passes on the
> golden one.

---

**The report is finished when there is a test in the suite that fails before the fix and passes
after.** `make verdict` is that, mechanised: row 2 is the failing test, row 3 is the fix.
