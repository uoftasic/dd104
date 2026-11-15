# Solutions: instructor only

One file per variant: what the bug is, why it hides, what catches it, and what it
is for. Nothing here goes to a student, and nothing here goes under `docs/`.

Every number in these files was measured on `hpretl/iic-osic-tools:2026.08`
(Icarus 14.0, cocotb 2.0.1). The runs that produced them are `../verify/`; the
per-variant table is `../verify/results.json`.

Two numbers appear in most files:

- suite: how the 10-test systematic suite (`../verify/test_suite.py`) scores
  on that variant at the lab default `clk_per_bit = 32`. The clean core scores 10/10.
- ALU sweep: 393,216 vectors, 6 ops × 256 × 256, against a spec model
  (`../verify/test_alu.py`, about 19 s). The clean core has 0 mismatches.

One fact is true of all thirteen: the TinyTapeout boilerplate test that shipped
with this chip passes on every one of them.
