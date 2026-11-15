# ORI writes R0 — the decision, and the evidence for it

**Status:** decided for DD104, 2026-08-25. Delegated by the team lead. **For review by the
RTL author.**

**Scope:** this decides what *DD104 teaches* and what the course's golden model implements.
It does not claim to decide what the upstream SimProc specification says. There is an ask for
the author at the bottom.

---

## The question

`src/simproc_system.sv` carries the same comment twice:

```systemverilog
// line 635, inside CYCLE_3
                    // rA <- RF[0]
                    rf_reg_a_in     = 2'b0; // change this to 1, to match SimProc

// line 689, inside CYCLE_5
                // RF[0] <- ALU out (change later to be SimProc accurate)
                    rf_reg_w_in     = 2'b0; // change this to 1, to match SimProc
```

`ORI` is the only instruction in the set with no register field: the opcode is the low three
bits (`3'b111`) and all five remaining bits `instr[7:3]` are the immediate. Its
source-and-destination register is therefore implicit in the hardware, and those two lines are
where the hardware picks it. Every instruction encoding and half of DD104's bug injections
depend on the answer.

**Upstream commit this decision is pinned to:**

```
repo   git@github.com:uoftasic/simproc.git   (branch main)
commit 1d97772cd933faeb5d330074d0dc58b07378f15c   "Merge pull request #1 ... vprajapati/mem-64"
       Vraj Prajapati, Mon Nov 10 12:06:29 2025 -0600
blob   src/simproc_system.sv  3c19a1b45c9b4e51f05f8ef73859ee13a4a3c329   (1178 lines)
sha256 5da82589f8b045a92f0390093118394f029df9723711aa957ecd2fcadfcf3dbe
```

The comments were introduced by `d3972ac` ("added wrapper template", SattiDaBeaver,
2025-11-10) and have never been touched since. Line numbers below are valid at that blob.

---

## What I did

I built four variants of the core and ran them, rather than reading them:

| variant | line 635 (read) | line 689 (write) | meaning |
|---|---|---|---|
| `base` | `2'b0` | `2'b0` | **as shipped** — `RF[0] <- RF[0] \| imm5` |
| `r1` | `2'b1` | `2'b1` | the comment applied to both sites — `RF[1] <- RF[1] \| imm5` |
| `splitw` | `2'b0` | `2'b1` | the comment applied to one site — `RF[1] <- RF[0] \| imm5` |
| `splitr` | `2'b1` | `2'b0` | the other single site — `RF[0] <- RF[1] \| imm5` |

Everything below was measured on `hpretl/iic-osic-tools:2026.08`, Icarus 14.0, cocotb 2.0.1,
driving the real `tt_um_ieeeuoftasic_simproc` pins through a bit-banged UART bus-functional
model at `clk_per_bit = 8`, with the register file and RAM read back through Icarus
hierarchical probes.

---

## Finding 1 — the shipped hardware writes R0, and it is self-consistent

One instruction, from reset:

```
[base]    ORI 5  ->  R0=5 R1=0 R2=0 R3=0
[r1]      ORI 5  ->  R0=0 R1=5 R2=0 R3=0
[splitw]  ORI 5  ->  R0=0 R1=5 R2=0 R3=0
[splitr]  ORI 5  ->  R0=5 R1=0 R2=0 R3=0
```

There is no third site: `rf_reg_b_in` is never set in the ORI path, so `reg_b_out` loads
`RF[0]` by default and nothing uses it. The shipped code reads and writes the same register,
which is the only property the instruction actually needs.

## Finding 2 — R0 and R1 are exactly isomorphic. Nothing in the RTL can break the tie.

I wrote a five-instruction program that builds the constant `20` and stores it at `0x20`, then
wrote the *same program with R0 and R1 swapped in every register field*, and ran each on each
core:

| program | on `base` | on `r1` |
|---|---|---|
| R0-flavour | `mem[0x20]=0x14 (20)`, `R=[20, 32, 0, 0]` | `mem[0x20]=0x00`, `R=[0, 20, 0, 0]` |
| R1-flavour | `mem[0x20]=0x00`, `R=[20, 0, 0, 0]` | `mem[0x20]=0x14 (20)`, `R=[32, 20, 0, 0]` |

The memory result is the same and the registers are mirrored. The symmetry is exact, because a
register index never leaves the instruction word in this design. `R0` is not hardwired to zero
(`register_file` is four symmetric bytes with a plain `rf[regW] <= dataW`), and no flag,
addressing mode, reset value or debug command treats either register specially; I checked all
1178 lines.

So all three tie-breakers the brief proposed come back with "no answer":

- **"which makes the instruction set coherent"** — both. The register is implicit either way;
  there is no other instruction whose behaviour depends on it.
- **"which makes the decoder unambiguous"** — both, identically. ORI is selected by
  `instr[2:0] == 3'b111` and the decoder never sees a register number for it. (Separately
  verified: the encoding has *no* opcode collisions at all. The two three-bit opcodes,
  `SHIFT = 011` and `ORI = 111`, alias only onto the low nibbles `B` and `F`, and neither is
  assigned to anything else. I confirmed this by single-stepping all 256 instruction bytes and
  classifying each by cycle count, `done`, PC delta, register write and memory write. The
  counts partition cleanly: 48 unimplemented (`C`,`D`,`E`), 64 branch (`1`,`5`,`9`,`A`),
  16 STORE (`2`), 80 four-cycle (`0`,`3`,`4`,`6`,`B`), 16 NAND (`8`), 32 ORI (`7`,`F`).)
- **"which makes the existing testbench pass"** — both. See Finding 4.

## Finding 3 — what *is* decidable: the two lines must move together

`splitw` and `splitr` are the interesting variants, because they are broken as an ISA: nobody
specified "OR the immediate into one register, write the answer to a different one" as an
instruction. Here is the measured difference on the same five-instruction program:

```
[base]    R0-flavour program -> mem[0x20]=0x14 (20)
[splitr]  R0-flavour program -> mem[0x20]=0x24 (36)
[r1]      R1-flavour program -> mem[0x20]=0x14 (20)
[splitw]  R1-flavour program -> mem[0x20]=0x24 (36)
```

The split variants are worth naming because the first `ORI` after reset is correct on both of
them: both registers are 0, and `0 | imm == imm` no matter which one you read. The divergence
only appears on the *second* `ORI`, once the other register is non-zero, so a smoke test that
does one `ORI` and checks the result cannot see it. That is why the half-applied edit is the
strongest bug injection in the DD104 catalogue rather than a footnote here.

## Finding 4 — the shipped test has no opinion about any of this

`test/test.py` is the TinyTapeout boilerplate. It sets `ui_in = 1`, `uio_in = 0`, waits 100
clocks and asserts `uo_out == 3`. Decoded against the wrapper, `3` is
`uart_tx = 1` (line idle), `halt = 1` (core in `IDLE`) and `done = 0`, so what it asserts is
that the processor is not running. It never sends a UART command, never loads a program and
never executes an instruction.

```
base   -> TESTS=1 PASS=1 FAIL=0
r1     -> TESTS=1 PASS=1 FAIL=0
splitw -> TESTS=1 PASS=1 FAIL=0
splitr -> TESTS=1 PASS=1 FAIL=0
```

It passes on all four, and it also passes against all thirteen deliberate bug injections in the
DD104 catalogue. The test is the shuttle template's, untouched, so this is no criticism of the
repo, but it does mean "make the existing testbench pass" cannot be used as evidence, and it is
the reason DD104 exists.

---

## The decision

> **DD104 specifies `ORI` as `RF[0] <- RF[0] | ZE(instr[7:3])`**, the behaviour the shipped
> RTL has today, and the DD104 fork **deletes the two `// change this to 1` comments**,
> replacing them with a single normative comment. No logic changes.

Since the hardware cannot break the tie, the tie-breakers are editorial:

1. **The fork stays byte-identical to `1d97772` in `src/`.** DD104's golden model, its
   assembler, every lab's expected numbers and every bug injection anchor to line numbers in a
   file we did not modify. That is worth more to a verification course than a preference about
   register naming.
2. **Choosing R1 buys a permanent merge conflict on the exact two lines upstream is most
   likely to touch**, in exchange for no observable behaviour difference.
3. **A "change this to 1" comment is a hazard in a course whose premise is "there are hidden
   bugs in this file".** It reads as a planted clue pointing at code that is correct, so it has
   to go whichever way the decision lands. That part is not negotiable.
4. **The R1 reading is worth more as a bug than as a spec.** `splitw` becomes catalogue entry
   **B11**, and the reset-aliasing in Finding 3 makes it one of the two hardest bugs in the set.

The exact edit to the fork:

```systemverilog
// line 635
                    // ORI's accumulator is R0 (DD104 spec; see ORI-DECISION.md)
                    rf_reg_a_in     = 2'b0;

// line 689
                    // RF[0] <- ALU out.  ORI's accumulator is R0 (DD104 spec).
                    rf_reg_w_in     = 2'b0;
```

**If the author confirms the reference SimProc uses R1**, the cost of following them is one
line in the golden model, one constant in the assembler, and an R0/R1 swap in the register
fields of about a dozen shipped example programs. Because the machines are isomorphic, nothing
else in DD104 changes, and no lesson is worth more under either reading. The decision is cheap
to reverse, and it is written so that it stays that way.

---

## Ask for the author

1. **Is the reference SimProc's `ORI` accumulator R0 or R1?** If the answer is on paper
   somewhere, a link settles this permanently.
2. **Whichever it is, please either apply the change to both sites or delete both comments
   upstream.** Applying it to one site produces `splitw`/`splitr`, which is a real bug that
   hides behind a reset (Finding 3).
3. Two smaller things found while reading, neither a bug report:
   - **`ALU` shifts by `B[1:0]`** (lines 814–815). Reachable only from the SHIFT instruction,
     whose amount field `instr[4:3]` is two bits anyway, so the truncation can't be observed
     through the ISA. A direct ALU unit test, though, sees it on **63,567 of 65,536** `(A,B)` vectors
     per shift direction. DD104 uses this as its "a unit test finds what an integration test
     structurally cannot" example. Intentional?
   - **`dp_ram` is 64 deep and addressed with 8 bits.** Verilator's default lint flags it four
     times (`Bit extraction of array[63:0] requires 6 bit index, not 8 bits`); Icarus compiles
     it and turns it into an `X` at run time. A UART `READ` of address `0x45` puts eight `X`
     bits on the chip's TX pin. Writes above 63 are silently dropped and don't alias into
     low memory (verified: `mem[0x05]` unchanged after writing `0x99` to `0x45`).
