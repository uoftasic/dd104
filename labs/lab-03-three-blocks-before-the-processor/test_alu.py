"""
DD104 Lab 03 — the ALU.  Thirty-three lines of RTL, and the whole input space
is 393,216 vectors, which Icarus will chew through while you read this.

    make alu        this file, against the golden ALU
    make check      the verdict: pass on the golden ALU, FAIL on a broken one

The ALU is combinational.  No clock, no state, no reset:

    module ALU (
        input  logic [2:0] ALUop,
        input  logic [7:0] A,
        input  logic [7:0] B,
        output logic       N,
        output logic       Z,
        output logic [7:0] ALUout
    );

3 + 8 + 8 = 19 bits of input, so 2**19 = 524,288 possible vectors.  Two of the
eight opcodes are unassigned, which leaves 6 x 256 x 256 = 393,216 that mean
anything.  Every single one of them can be driven, in about twenty seconds.

That is the argument for unit testing in one paragraph.  You cannot exhaustively
test the 1,178-line processor — it has 64 bytes of memory and a program counter,
so its state space is astronomical.  You *can* exhaustively test its ALU, and
after you have, every failure in the processor above it is a failure somewhere
that is not the ALU.  Verification is largely the business of shrinking the
place a bug could be hiding.
"""

import cocotb
from cocotb.triggers import Timer

# The opcode encoding, straight out of the RTL's typedef.
ADD, SUB, OR, NAND, SHL, SHR = 0, 1, 2, 3, 4, 5
OPS = {ADD: "ADD", SUB: "SUB", OR: "OR", NAND: "NAND", SHL: "SHL", SHR: "SHR"}


def spec(op, a, b):
    """What the ALU is supposed to produce.  Returns (out, N, Z).

    This is a specification, written from the ISA and not from the RTL.  If you
    write it by reading the Verilog you have built a machine that agrees with
    the design about everything including its bugs, which is the single most
    common way a verification effort wastes six months.

    Two details worth having in your hands before you look at any waveform:

      * The shifts use only `B[1:0]`, so the shift amount is 0-3 and never
        more.  Nothing in the instruction set can ask for a bigger shift.
      * N and Z are functions of the *result*, not of the operands. N is
        literally bit 7 of the output; Z is 'the output is all zeroes'. There
        is no carry flag and no overflow flag on this machine.
    """
    if op == ADD:
        out = (a + b) & 0xFF
    elif op == SUB:
        out = (a - b) & 0xFF
    elif op == OR:
        out = a | b
    elif op == NAND:
        out = (~(a & b)) & 0xFF
    elif op == SHL:
        out = (a << (b & 3)) & 0xFF
    elif op == SHR:
        out = a >> (b & 3)
    else:
        out = 0
    return out, (out >> 7) & 1, int(out == 0)


async def alu(dut, op, a, b):
    """Drive one vector and read the three outputs back."""
    dut.ALUop.value = op
    dut.A.value = a
    dut.B.value = b
    await Timer(1, unit="ns")
    return int(dut.ALUout.value), int(dut.N.value), int(dut.Z.value)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  One vector per operation, chosen on purpose
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t01_one_vector_per_operation(dut):
    """Six vectors.  Every one of them uses two different operand values.

    That is the whole design of this test.  The natural directed vectors —
    `SUB(x, x)` for 'clear', `NAND(x, x)` for 'not' — are exactly the ones a
    swapped subtractor and a NAND-that-is-really-NOR both survive."""
    cases = [
        (ADD,  200, 60),
        (SUB,  200, 60),
        (OR,   0xF0, 0x0F),
        (NAND, 0xC3, 0x1D),
        (SHL,  0x21, 2),
        (SHR,  0xF8, 3),
    ]
    for op, a, b in cases:
        got = await alu(dut, op, a, b)
        want = spec(op, a, b)
        assert got == want, (
            f"{OPS[op]}(0x{a:02X}, 0x{b:02X}) gave out=0x{got[0]:02X} "
            f"N={got[1]} Z={got[2]}, expected out=0x{want[0]:02X} "
            f"N={want[1]} Z={want[2]}")
    dut._log.info(f"{len(cases)} directed vectors, all correct")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Exhaustive — on the values
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t02_every_vector_the_alu_can_be_given(dut):
    """All 393,216 legal vectors, checking `ALUout` and nothing else.

    Takes about twenty seconds.  Bugs cannot hide in an unexplored corner of
    the input space here, because there is no unexplored corner.

    Note carefully what is *not* checked: N and Z are read and thrown away.
    That is deliberate, it is the most common shape of real testbench, and
    `make check BUG=B03` is about to show you what it costs.

    ── TODO ──────────────────────────────────────────────────────────────────
    `spec()` already returns the two flags.  Compare them.

    The shape is a second bucket, kept separately from the value mismatches:

        if got[0] != want[0]:
            bad_values.append(...)
        if got[1:] != want[1:]:
            bad_flags.append((op, a, b, got, want))

    Keep the two counts apart and report both.  A run that says
    `0 value mismatches, 3840 flag mismatches on ADD` has already told you the
    fault is in the flag logic and not in the adder, before you open a
    waveform — and it has told you *which* 3840, because 3840 = 15 x 256 and
    that factorisation is a sentence about the bug.
    ──────────────────────────────────────────────────────────────────────────
    """
    bad_values = []
    checked = 0

    for op in OPS:
        for a in range(256):
            for b in range(256):
                got = await alu(dut, op, a, b)
                want = spec(op, a, b)
                checked += 1
                if got[0] != want[0]:
                    bad_values.append((op, a, b, got[0], want[0]))

    per_op = {}
    for op, a, b, g, w in bad_values:
        per_op[OPS[op]] = per_op.get(OPS[op], 0) + 1

    dut._log.info(f"{checked} vectors checked, "
                  f"{len(bad_values)} value mismatches {per_op or ''}")

    if bad_values:
        op, a, b, g, w = bad_values[0]
        raise AssertionError(
            f"{len(bad_values)} of {checked} vectors have the wrong value: "
            f"{per_op}.\n"
            f"  First one: {OPS[op]}(0x{a:02X}, 0x{b:02X}) = 0x{g:02X}, "
            f"expected 0x{w:02X}.\n"
            f"  The per-operation counts above are the diagnosis. An operation "
            f"with 0 mismatches is not the one that is broken.")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  The two opcodes nobody specified
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t03_the_undefined_opcodes(dut):
    """ALUop 6 and 7 are not in the enum.  They still do something.

    The `case` has a `default: ALUout = 8'h00;`, so opcodes 6 and 7 return
    zero — which also means N = 0 and Z = 1, a perfectly ordinary-looking
    'the answer was zero'.

    This test asserts the behaviour the RTL happens to have, which is a thing
    to do carefully and knowingly.  It is not in any specification. It is
    pinned here so that if somebody changes it — to an X, to a trap, to a
    passthrough — a test goes red and a human decides whether that was
    intended.  A test can be a record of a decision as well as a check of a
    requirement, and the comment is what tells the next reader which one it is.
    """
    for op in (6, 7):
        out, n, z = await alu(dut, op, 0xAB, 0xCD)
        assert (out, n, z) == (0, 0, 1), (
            f"ALUop {op} gave out=0x{out:02X} N={n} Z={z}, expected "
            f"out=0x00 N=0 Z=1 (the case default)")
    dut._log.info("opcodes 6 and 7 both return 0x00, with N=0 Z=1")
