# bug-03

> "The arithmetic is fine. I've checked dozens of results and every single value
> is correct. What's wrong is that my branches go the wrong way."

## What was seen

```
SUB r0,r0        R0 = 0
ORI 16           R0 = 16      -- not zero
BZ  +1           branch if the last result was zero
ORI 1            R0 = 17      -- this must run; 16 is not zero
```

| | R0 |
|---|---|
| should be | **17** — the branch is not taken, the `ORI 1` runs |
| this core | **16** — the branch was taken and skipped it |

The value in R0 after `ORI 16` really is 16. Read it back and it is 16. The
machine still decided that 16 was zero.

Something is right in one place and wrong in another, at the same instant, about
the same number.

## What you have

`src/` — the core: 1178 + 49 lines of SystemVerilog. One line of it is wrong.
`test/` — the testbench that shipped with this chip.

```bash
cd test && make -B
```

It passes.

## What finishing looks like

1. A test that **fails** on this core and would pass on a correct one.
2. The one-line fix.
3. That same test passing.

If your test only compares results, you will not catch this one no matter how
many results you compare. Six hundred randomly generated instructions were tried
and every one of them passed.
