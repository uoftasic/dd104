# Lab 03 — Three blocks before the processor

Full runnable package: [`labs/lab-03-three-blocks-before-the-processor/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-03-three-blocks-before-the-processor).

SimProc is 1,178 lines and you cannot test all of it. Three of its modules are 16, 31 and 34
lines, and you can test all of those — completely, in the strong sense, until there is no
behaviour left in them that is untested.

This lab is where a processor stops being one intimidating object and becomes a small number of
tractable ones.

## Prerequisites

- [Lab 02](labs/lab-02-the-only-test-this-chip-has-overview.md) complete — you have produced `13 of 13`
- Read [The lazy testbench](guide/the-lazy-testbench.md),
  [Coverage as a question](guide/coverage-is-a-question.md) and
  [Flags are architectural state](guide/flags-are-state.md) *(not yet written)*
- [SimProc in one page](guide/simproc-in-one-page.md) open in another tab

## Objectives

- Elaborate a single submodule of a large design as the simulation top level
- Test a 16-line module until it is *finished*, and be able to defend the word
- Drive all **393,216** legal vectors through an ALU and check every one
- Derive three exact failure counts by hand, before or after measuring them
- Discover a testbench that sweeps the entire input space and still misses a bug
- Find one architectural fact about SimProc that changes how you read every later lab

## Theory (short)

**The prior this lab overwrites:** *to test a module you need the chip around it.*

You do not. cocotb hands the simulator a list of source files and the name of one module to
elaborate as the top level. Give it `simproc_system.sv` and `TOPLEVEL=ALU`, and Icarus compiles
all 1,178 lines and then builds a design whose only contents are the ALU. The other 1,100 lines
are compiled and simply not connected to anything. There is no processor, no clock, no memory —
just three input ports and three output ports.

That is the whole mechanism, and it changes the arithmetic completely:

|  | inputs | possible vectors | exhaustive? |
|---|---|---|---|
| `program_counter` | `rst`, `pc_wr`, `pc_in[7:0]` + one register of state | 4 distinct behaviours | **yes**, by cases |
| `register_file` | `rst`, `RFWrite`, three 2-bit selects, `dataW[7:0]` + 32 bits of state | small | **yes**, by cases |
| `ALU` | `ALUop[2:0]`, `A[7:0]`, `B[7:0]`, no state | $2^{19} = 524{,}288$, of which 393,216 are legal | **yes**, by brute force |
| `simproc` | all of the above plus 64 bytes of RAM and a PC | astronomical | **no** |

A small block can be finished. A processor cannot. So you finish the small blocks, and then
every failure in the processor above them is a failure somewhere that is not those blocks.
**Verification is largely the business of shrinking the place a bug could be hiding.**

### The ALU's behaviour

Excerpt from [`labs/common/rtl/simproc_system.sv`](https://github.com/uoftasic/dd104/blob/main/labs/common/rtl/simproc_system.sv),
module `ALU`, lines 790–823. The port list and the `aluop_t` enum are omitted; this is the
whole of the logic.

```systemverilog
always @ (*) begin
    case(ALUop)
        ADD:     ALUout = A + B;
        SUB:     ALUout = A - B;
        OR:      ALUout = A | B;
        NAND:    ALUout = ~(A & B);
        SHL:     ALUout = A << B[1:0];
        SHR:     ALUout = A >> B[1:0];
        default: ALUout = 8'h00;
    endcase
end
assign N = ALUout[7];
assign Z = ~(|ALUout);
```

Two facts to have in your hands before you write a spec model. The shifts use only `B[1:0]`,
so the shift amount is 0–3 and nothing in the instruction set can ask for more. And `N` and `Z`
are functions of the *result*: `N` is literally bit 7 of the output, `Z` is "the output is all
zeroes". There is no carry flag and no overflow flag on this machine.

> **Write the spec model from the ISA, not from the Verilog.** If you write `spec()` by reading
> the RTL you have built something that agrees with the design about everything, including its
> bugs. That is the single most common way a verification effort wastes six months.

## Procedure

```bash
mod dd104
cd labs/lab-03-three-blocks-before-the-processor
make
```

About **a minute** for everything. The individual targets are much faster and are the ones
you will actually use.

### Step 1 — A module that can be finished: `program_counter`

- **Try this:** `make pc`. About **3 seconds**.
- **What you should see:**

  ```
  ** test_pc.t01_reset_makes_it_zero   PASS          21.00 **
  ** test_pc.t02_load_when_pc_wr       PASS        2571.00 **
  ** test_pc.t03_hold_when_not_pc_wr   PASS          61.00 **
  ** test_pc.t04_reset_beats_load      PASS          21.00 **
  ** TESTS=4 PASS=4 FAIL=0 SKIP=0                  2674.00 **
  ```

  All five simulated-time figures are **GOLDEN**.

- **Why an engineer cares:** `test_pc.py` ships complete, and it is the model for everything
  else you write in this lab. The module is an 8-bit register with a synchronous reset and a
  load enable, and there are exactly four things it can be asked to do — reset, load, hold, and
  reset-while-loading. All four are tested. There is nothing left.

  Two of the four are the ones people skip, and they are the ones that matter:

  - **`t03_hold_when_not_pc_wr`** drives junk on `pc_in` with `pc_wr` low and checks that
    nothing moved. A PC that loads correctly and never holds passes `t02` perfectly.
  - **`t04_reset_beats_load`** raises `rst` and `pc_wr` together. Priority between two control
    inputs is a decision somebody made, it is invisible from the port list, and the next person
    to touch this file can reverse it by swapping two branches.

  Read the file. It is 120 lines including comments, and everything you need for `test_rf.py`
  is in it: drive on one edge, sample after the other, and never let your stimulus race the
  DUT's clock.

### Step 2 — A module with a surprise in it: `register_file`

- **Try this:** `make rf`. It ships with two tests passing and three TODOs.
- **What you should see:** `TESTS=2 PASS=2`, `51.00` ns total — **GOLDEN**.
- **Why an engineer cares:** the TODOs are `t03`, `t04` and `t05`, and `t03` is the one to do
  first.

  Most small processors hardwire register 0 to the constant zero. RISC-V's `x0` reads as zero
  and discards writes. MIPS's `$zero` does the same. It is common enough that assuming it here
  is a completely reasonable thing to do.

  **Check it.** Write `0xFF` into r0 and read it back. Then write a *different* value and read
  it again — one write landing is not proof, because a file that latched the first write and
  then stuck would also pass.

  What you find changes how you read every `ORI` instruction in this course, and it is better
  to find it now than at 1 a.m. in [Lab 06](labs/lab-06-capstone-overview.md).

  `t04` and `t05` are the two shapes that recur everywhere: *one write moves one register*, and
  *an enable that is not enabling anything*. Run `t05` for several cycles rather than one —
  "it did not write on the first edge" and "it does not write" are different claims, and only
  the second one is the requirement.

### Step 3 — The early win: all 393,216 ALU vectors

- **Try this:** `make alu`. About **23 seconds**, and 20 of them are `t02`.
- **What you should see:**

  ```
  393216 vectors checked, 0 value mismatches
  ** test_alu.t01_one_vector_per_operation            PASS           6.00 **
  ** test_alu.t02_every_vector_the_alu_can_be_given   PASS      393216.00 **
  ** test_alu.t03_the_undefined_opcodes               PASS           2.00 **
  ** TESTS=3 PASS=3 FAIL=0 SKIP=0                               393224.00 **
  ```

  **`393216`, `0 value mismatches` and `393224.00` are GOLDEN.**

- **Why an engineer cares:** six operations × 256 × 256, every legal vector this module can be
  given, checked against a specification model, in the time it takes to read this paragraph.
  Bugs cannot hide in an unexplored corner of the input space, because there is no unexplored
  corner.

  Take exhaustive when it is available. It usually is not — an 8-bit multiplier pair is 65,536
  vectors and fine, an 8-bit ALU with a 3-bit opcode is 524,288 and fine, and a 32-bit adder is
  $2^{65}$ and never happening — but the moment a block is small enough, brute force beats
  cleverness and beats it decisively.

### Step 4 — Two bugs, and the number is the diagnosis

- **Try this:** `make check BUG=B01`, then `make check BUG=B02`.
- **What you should see:** both `caught`, both with a count in the message:

  ```
  65024 of 393216 vectors have the wrong value: {'SUB': 65024}.
    First one: SUB(0x00, 0x01) = 0x01, expected 0xFF.
  ```
  ```
  65280 of 393216 vectors have the wrong value: {'NAND': 65280}.
    First one: NAND(0x00, 0x01) = 0xFE, expected 0xFF.
  ```

  **`65024` and `65280` are GOLDEN**, and so are the per-operation dictionaries. Every other
  operation reports zero, which is itself part of the diagnosis: *an operation with 0
  mismatches is not the one that is broken.*

- **Why an engineer cares:** now derive both counts by hand, because the derivation is the
  lab and the counts are only the check.

  **`B01`, 65,024 of 65,536 `SUB` vectors.** The survivors are the pairs where $A - B$ and
  $B - A$ are the same byte. That happens when $2(A-B) \equiv 0 \pmod{256}$, i.e. when
  $A - B \equiv 0$ or $A - B \equiv 128$. Each congruence has 256 solutions, so
  $256 + 256 = 512$ survivors and $65{,}536 - 512 = 65{,}024$ failures.

  And **`SUB rX, rX` — the idiom for clearing a register, which appears in nearly every program
  on this machine — is one of the 512.**

  **`B02`, 65,280 of 65,536 `NAND` vectors.** $\lnot(A \wedge B) = \lnot(A \vee B)$ exactly when
  $A \wedge B = A \vee B$, which is exactly when $A = B$. That is 256 survivors, and
  $65{,}536 - 256 = 65{,}280$.

  And in a four-register machine with no `NOT` instruction, **`NAND rX, rX` *is* how you write
  `NOT`** — which makes it the most common `NAND` anybody writes, and it is precisely the case
  where the bug is invisible.

  Both bugs survive the single most idiomatic use of the instruction they break. That is not a
  coincidence in the catalogue; it is what makes a bug survive review.

### Step 5 — The moment: a clean sweep on a broken chip

- **Try this:** `make check BUG=B03`, with the shipped `test_alu.py` — the one that checks
  `ALUout` and throws the flags away.
- **What you should see:**

  ```
        ok  the golden ALU                     3 tests, all passed         20.5s
    MISSED  B03_zero_flag_low_nibble           3 tests, all passed         21.3s
  ------------------------------------------------------------------------
   VERDICT: FAIL -- test_alu passes B03_zero_flag_low_nibble too.
     That bug hides behind: every test that checks results and not flags
  ```

- **Why an engineer cares:** 393,216 vectors. Every one of them driven. Every one of them
  correct. `0 value mismatches`, on a core that is broken.

  A value-only testbench does not *usually* miss this bug. It **cannot** see it, at all, ever,
  no matter how many vectors you add — because the values are not what is wrong. More stimulus
  is not the missing ingredient. A different *kind* of check is.

  Flags are architectural state. Every branch you will write in
  [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md) depends on them. See
  [Flags are architectural state](guide/flags-are-state.md).

### Step 6 — Add the flags, and read the shape

- **Try this:** do the TODO in `t02`. `spec()` already returns `(out, N, Z)`; compare all three,
  and keep the value mismatches and the flag mismatches in **separate buckets**.
- **What you should see:** `make check-alu-bugs` now reports `3 of 3`, and `B03` fails with:

  ```
  393216 vectors checked -- 0 value mismatches , 25726 flag mismatches
  {'ADD': 3840, 'SUB': 3840, 'OR': 255, 'NAND': 255, 'SHL': 14400, 'SHR': 3136}
  ```

  **All eight of those numbers are GOLDEN.**

> **`3 of 3` is only worth having if it counts checks and not crashes.** A student's `t02` once
> reported exactly that from a testbench whose failure message referred to a variable that was
> never assigned. `NameError` never fires while everything is correct, so the testbench passed
> the golden ALU and crashed on all three broken ones — and the old `check.py`, which read
> cocotb's `<failure>` elements without looking at `error_type`, called three crashes three
> catches. The verdict now says
>
> ```
>  NO COUNT. 3 of the 3 runs did not finish:
>    B01_sub_operands_swapped: t02_every_vector_the_alu_can_be_given BLEW UP
>       NameError: name 'value_per_op' is not defined
> ```
>
> and prints no number at all, because there is no number to print. Watch for it when you write
> the two-bucket report in this step: the report only executes when something is wrong, which
> is the one condition under which you never test it.

- **Why an engineer cares:** `0 value mismatches, 25,726 flag mismatches` is a diagnosis. It
  says the arithmetic is fine and the flag logic is not, before anybody opens a waveform. One
  combined count of 25,726 would have said far less, and that is the entire reason for two
  buckets instead of one.

  Now close two of the six by hand. The bug makes `Z` wrong exactly when the result is non-zero
  but its low four bits are zero — that is 15 possible results: `0x10`, `0x20`, … `0xF0`.

  **ADD: 3,840.** For any target byte $t$, exactly 256 pairs $(A,B)$ satisfy
  $A + B \equiv t$. Fifteen targets, 256 pairs each: $15 \times 256 = 3840$. `SUB` is identical.

  **OR: 255.** $A \vee B$ has a zero low nibble only when $A[3{:}0] = B[3{:}0] = 0$, which is
  $16 \times 16 = 256$ pairs. One of those — $A = B = 0$ — produces a genuinely zero result,
  which a low-nibble detector gets right by accident. $256 - 1 = 255$.

  Do `NAND` yourself; it is the same argument with `0xF` in place of `0`. `SHL` (14,400) and
  `SHR` (3,136) need one sum over the four shift amounts each and are worth the ten minutes.

  When a failure count factors that cleanly, **the factors are describing the bug.**

### Step 7 — A defined answer for an undefined opcode

- **Try this:** read `t03_the_undefined_opcodes`, which ships passing.
- **What you should see:** `ALUop` 6 and 7 both return `0x00`, with `N=0` and `Z=1`.
- **Why an engineer cares:** those two opcodes are not in the enum. The `case` has a
  `default: ALUout = 8'h00;`, so they return zero — which also means `Z` is set, and a zero
  result with `Z` set is a perfectly ordinary-looking answer. Nothing downstream can tell "the
  answer was zero" from "that was not an instruction".

  **"Defined" and "correct" are different words.** This behaviour is not in any specification;
  it is what the RTL happens to do. `t03` pins it so that if somebody changes it — to an X, to a
  trap, to a passthrough — a test goes red and a human decides whether that was intended. A
  test can be a record of a decision as well as a check of a requirement, and the comment above
  it is what tells the next reader which one it is.

## Expected results

| Check | Expected | |
|---|---|---|
| `make pc` | `TESTS=4 PASS=4`, `2674.00` ns | **GOLDEN** |
| `make rf`, shipped | `TESTS=2 PASS=2`, `51.00` ns | **GOLDEN** |
| `make rf`, finished | `TESTS=5 PASS=5` | |
| `make alu` | `393216 vectors checked, 0 value mismatches`, `393224.00` ns | **GOLDEN** |
| `make alu` wall clock | about 23 s | BALLPARK |
| `B01` | `{'SUB': 65024}` value mismatches | **GOLDEN** |
| `B02` | `{'NAND': 65280}` value mismatches | **GOLDEN** |
| `B03`, values only | **`MISSED`** — 0 mismatches | **GOLDEN** |
| `B03`, with flags | 0 value, `25726` flag: `{'ADD': 3840, 'SUB': 3840, 'OR': 255, 'NAND': 255, 'SHL': 14400, 'SHR': 3136}` | **GOLDEN** |
| `make check-alu-bugs` when done | `3 of 3 ALU bugs caught` | |

`make check-alu-bugs` takes about **90 seconds** — four full builds and four exhaustive sweeps.
That is BALLPARK; the `3 of 3` is not.

> **The `sorry:` notes are still there.** 28 of them, on every compile, including these
> unit-level ones. See [Output that is not an error](reference/output-that-is-not-an-error.md).

## Going further

The catalogue has thirteen bugs and this lab reached **three**. The other ten are in the control
path around the ALU — decode, write-back, branching, the handshake — where a unit test of the
ALU structurally cannot see them. `make check-alu-bugs` says so in its own closing line.

That is the honest limit of unit testing, and it is worth stating plainly rather than
discovering: finishing a block proves the block is right. It says nothing about whether the
right block is being used, with the right operands, at the right time. Which is
[Lab 04](labs/lab-04-your-first-bug-hunt-overview.md).

## Links

- [Lab package](https://github.com/uoftasic/dd104/tree/main/labs/lab-03-three-blocks-before-the-processor)
- [Flags are architectural state](guide/flags-are-state.md) — why Step 5 is the moment this lab exists for
- [Coverage as a question](guide/coverage-is-a-question.md) — a different way to ask what Step 5 asks
- [The SimProc instruction set](reference/simproc-instruction-set.md) — the ISA the spec model comes from
- Next lab: [Lab 04 — Your first bug hunt](labs/lab-04-your-first-bug-hunt-overview.md), where nobody tells you which bug you have
