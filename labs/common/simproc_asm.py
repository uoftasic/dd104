"""
DD104 — a SimProc assembler, in about 200 lines of plain Python.

SimProc instructions are one byte.  You *can* write test programs as raw hex,
and your first instinct will be to do exactly that:

    prog = [0x2F, 0x44, 0xD9]     # ... which of these is the loop?

Two weeks later nobody can read that, including you.  So write mnemonics:

    from simproc_asm import *

    prog = [ORI(5),        # R0 = R0 | 5
            ADD(1, 0),     # R1 = R1 + R0
            STORE(1, 2)]   # mem[R2] = R1

or, when the program has a loop, write it as text and let labels do the
displacement arithmetic for you:

    prog = assemble('''
            ORI   5              # R0 = 5
            ADD   r1, r0         # R1 = 5
    loop:   SUB   r1, r0         # R1 -= 5
            BNZ   loop           # ... until it hits zero
            STORE r1, r2
    ''')

This module imports nothing.  It is not a cocotb thing — you can run it at a
plain Python prompt, and `python3 simproc_asm.py 0x2F 0x44` disassembles bytes
from the command line.  When a test fails and you are staring at a byte, that
is the fastest way to find out what it was.

────────────────────────────────────────────────────────────────────────────
THE INSTRUCTION SET
────────────────────────────────────────────────────────────────────────────
Every instruction is 8 bits.  Three field layouts share the byte:

    register form   A A B B o o o o     rA = bits[7:6], rB = bits[5:4]
    branch form     d d d d o o o o     4-bit SIGNED displacement in [7:4]
    3-LSB forms     A A D S S 0 1 1     SHIFT: D = direction, SS = amount
                    i i i i i 1 1 1     ORI:   5-bit immediate

  op     mnemonic  what it does                                     cycles
  0000   LOAD      rA <- mem[rB]                                      4
  0001   JMP       PC <- PC+1 + disp                  (always)        3
  0010   STORE     mem[rB] <- rA                                      3
  0011   SHIFT     rA <- rA << amt  or  rA >> amt                     4
  0100   ADD       rA <- rA + rB              sets N,Z                4
  0101   BPZ       if N==0: PC <- PC+1 + disp                         3
  0110   SUB       rA <- rA - rB              sets N,Z                4
  0111   ORI       R0 <- R0 | imm5            sets N,Z                5
  1000   NAND      rA <- ~(rA & rB)           sets N,Z                4
  1001   BNZ       if Z==0: PC <- PC+1 + disp                         3
  1010   BZ        if Z==1: PC <- PC+1 + disp                         3
  1011   (SHIFT again — the 3-LSB alias)                              4
  1111   (ORI again — the 3-LSB alias)                                5
  1100
  1101   UNIMPLEMENTED: 4 cycles, PC+1, nothing else happens,
  1110                  `done` never pulses, and `halt` blips high for
                        one of those four cycles

Four things about this ISA that will bite you if you skip them:

  * There are FOUR registers, r0..r3, and **r0 is an ordinary register**.  It
    is not hardwired to zero.
  * **ORI always writes r0**, whatever else is going on.  It has no register
    field — all five spare bits are the immediate.  (See ORI-DECISION.md for
    why the course says r0 and not r1.)
  * **Flags come from ADD, SUB, NAND, SHIFT and ORI only.**  LOAD, STORE and
    every branch leave N and Z exactly as they were.  That is a feature: you
    can compare once and branch on it twice.
  * There is **no NOT instruction**.  `NAND rX, rX` is how you write one, and
    there is **no compare instruction** — `SUB` is how you compare, which
    means comparing destroys one of the values.
"""

# ── register-form instructions ───────────────────────────────────────────────
# rA is both a source and the destination.  `ADD(1, 2)` means `r1 = r1 + r2`.

def LOAD(rA, rB):
    """rA <- mem[rB].  rB is the POINTER, rA is where the byte lands."""
    return _reg(rA, rB, 0b0000)

def STORE(rA, rB):
    """mem[rB] <- rA.  Same order as LOAD: data register first, pointer second."""
    return _reg(rA, rB, 0b0010)

def ADD(rA, rB):
    """rA <- rA + rB, 8-bit wraparound.  Sets N and Z.  No carry out anywhere."""
    return _reg(rA, rB, 0b0100)

def SUB(rA, rB):
    """rA <- rA - rB, 8-bit wraparound.  Sets N and Z.

    `SUB(x, x)` is the idiom for 'clear rX', and it is also the idiom that
    hides a swapped-operand bug, because A - B == B - A whenever A == B."""
    return _reg(rA, rB, 0b0110)

def NAND(rA, rB):
    """rA <- ~(rA & rB).  Sets N and Z.  `NAND(x, x)` is how you write NOT."""
    return _reg(rA, rB, 0b1000)


# ── shifts ───────────────────────────────────────────────────────────────────
# The amount is TWO BITS: 0, 1, 2 or 3.  You cannot shift by 4 in one
# instruction, and `SHL(0, 4)` is a mistake this assembler refuses to make
# quietly.

def SHL(rA, amount):
    """rA <- rA << amount, for amount in 0..3.  Sets N and Z."""
    return _shift(rA, amount, left=True)

def SHR(rA, amount):
    """rA <- rA >> amount (logical, zeros in), for amount in 0..3."""
    return _shift(rA, amount, left=False)


# ── the immediate ────────────────────────────────────────────────────────────

def ORI(imm5):
    """r0 <- r0 | imm5, for imm5 in 0..31.  Sets N and Z.  Always r0."""
    if not 0 <= imm5 <= 31:
        raise ValueError(f"ORI immediate {imm5} does not fit in 5 bits (0..31)")
    return (imm5 << 3) | 0b111


# ── branches ─────────────────────────────────────────────────────────────────
# The displacement is measured from the instruction AFTER the branch, because
# the PC has already been incremented by the time the branch computes its
# target:
#
#       target = (address of the branch) + 1 + disp
#
# so `JMP(0)` falls through, `JMP(1)` skips one instruction, and `JMP(-1)` is
# an infinite loop on itself.  Range is -8 .. +7 and nothing else.

def JMP(disp):
    """PC <- PC+1+disp, unconditionally."""
    return _branch(0b0001, disp)

def BPZ(disp):
    """Branch if the last flag-setting result was Positive-or-Zero (N == 0)."""
    return _branch(0b0101, disp)

def BNZ(disp):
    """Branch if the last flag-setting result was Non-Zero (Z == 0)."""
    return _branch(0b1001, disp)

def BZ(disp):
    """Branch if the last flag-setting result was Zero (Z == 1)."""
    return _branch(0b1010, disp)


# ── not an instruction ───────────────────────────────────────────────────────

def UNIMP():
    """Opcode 0xC: four cycles, PC+1, no state change, and no `done` pulse.

    Four, not three: it matches no clause in CYCLE_3, so the FSM falls to its
    default exit — IDLE — and spends a cycle there before `run` sends it back
    to CYCLE_1.  `halt` is high for that one cycle.  Measured.

    Useful as memory filler.  If the core runs off the end of your program it
    will walk through these harmlessly instead of executing whatever byte
    happened to be lying there."""
    return 0x0C


# ── a convenience that is not an instruction ─────────────────────────────────

def set_reg(reg, value):
    """Return the instructions that put an arbitrary 0..255 `value` in `reg`.

    ORI is the only way to get a constant into the machine, it ORs rather than
    loads, its immediate is 5 bits, and it only ever writes r0.  So building
    the byte 0xB7 takes four instructions:

        SUB r0, r0     # r0 = 0        (OR only sets bits; you must clear first)
        ORI 0x16       # r0 = value >> 3      (the top five bits)
        SHL r0, 3      # r0 = value & 0xF8    (shove them up)
        ORI 0x07       # r0 = value           (the bottom three)

    and two more if the destination is not r0.  Always 4 instructions for r0,
    always 6 for r1/r2/r3, so you can still predict the cycle count.

    ⚠ This CLOBBERS N and Z (SUB, ORI and SHIFT all set flags).  If you are
    testing branch behaviour, set your registers up *before* the compare, never
    between the compare and the branch."""
    if not 0 <= value <= 255:
        raise ValueError(f"set_reg value {value} does not fit in a byte")
    prog = [SUB(0, 0), ORI(value >> 3), SHL(0, 3), ORI(value & 0b111)]
    if reg != 0:
        prog += [SUB(reg, reg), ADD(reg, 0)]
    return prog


# ── the text front end ───────────────────────────────────────────────────────

_MNEMONICS = {
    "LOAD": ("reg", LOAD), "STORE": ("reg", STORE), "ADD": ("reg", ADD),
    "SUB": ("reg", SUB),   "NAND": ("reg", NAND),
    "SHL": ("shift", SHL), "SHR": ("shift", SHR),
    "ORI": ("imm", ORI),
    "JMP": ("branch", JMP), "BPZ": ("branch", BPZ),
    "BNZ": ("branch", BNZ), "BZ": ("branch", BZ),
    "UNIMP": ("none", UNIMP),
}


def assemble(text, base=0):
    """Assemble a program written as text.  Returns a list of byte values.

    One instruction per line.  `#` starts a comment.  A bare word followed by
    `:` is a label, and a branch may name a label instead of a number:

        assemble('''
        loop:   SUB   r1, r0
                BNZ   loop
        ''')

    `base` is the address the program will be loaded at; it only matters if
    you also write numeric branch targets, which you should not.

    Errors name the line.  A branch to a label more than 7 forward or 8 back
    is a hard error, not a silent wrap — that displacement genuinely does not
    fit in the instruction."""
    # Pass 1: strip comments, find labels, and count instructions.
    items = []          # (source_line_no, text, address)
    labels = {}
    addr = base
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#")[0].strip()
        while ":" in line:
            label, line = line.split(":", 1)
            label, line = label.strip(), line.strip()
            if not label.isidentifier():
                raise SyntaxError(f"line {lineno}: '{label}:' is not a usable label")
            if label in labels:
                raise SyntaxError(f"line {lineno}: label '{label}' defined twice")
            labels[label] = addr
        if line:
            items.append((lineno, line, addr))
            addr += 1

    # Pass 2: encode, now that every label has an address.
    out = []
    for lineno, line, at in items:
        out.append(_encode(lineno, line, at, labels))
    return out


def _encode(lineno, line, at, labels):
    parts = line.replace(",", " ").split()
    mnem = parts[0].upper()
    args = parts[1:]
    if mnem not in _MNEMONICS:
        raise SyntaxError(f"line {lineno}: '{parts[0]}' is not a SimProc instruction. "
                          f"Known: {', '.join(sorted(_MNEMONICS))}")
    kind, fn = _MNEMONICS[mnem]
    try:
        if kind == "none":
            _want(lineno, args, 0, mnem)
            return fn()
        if kind == "reg":
            _want(lineno, args, 2, mnem)
            return fn(_reg_num(lineno, args[0]), _reg_num(lineno, args[1]))
        if kind == "shift":
            _want(lineno, args, 2, mnem)
            return fn(_reg_num(lineno, args[0]), _int(lineno, args[1]))
        if kind == "imm":
            _want(lineno, args, 1, mnem)
            return fn(_int(lineno, args[0]))
        # branch: either a label or a signed number
        _want(lineno, args, 1, mnem)
        tok = args[0]
        if tok in labels:
            disp = labels[tok] - (at + 1)
            if not -8 <= disp <= 7:
                raise ValueError(
                    f"'{tok}' is {disp:+d} instructions away and a SimProc branch "
                    f"only reaches -8..+7. Move the label closer, or JMP to a JMP.")
            return fn(disp)
        if tok.isidentifier():
            raise SyntaxError(f"line {lineno}: no label named '{tok}'. "
                              f"Defined: {', '.join(sorted(labels)) or '(none)'}")
        return fn(_int(lineno, tok))
    except (ValueError, SyntaxError) as e:
        raise type(e)(f"line {lineno}: {line!r}: {e}") from None


def _want(lineno, args, n, mnem):
    if len(args) != n:
        raise SyntaxError(f"{mnem} takes {n} operand(s), got {len(args)}")


def _reg_num(lineno, tok):
    t = tok.lower()
    if t.startswith("r") and t[1:].isdigit() and 0 <= int(t[1:]) <= 3:
        return int(t[1:])
    raise ValueError(f"'{tok}' is not a register. SimProc has r0, r1, r2, r3.")


def _int(lineno, tok):
    try:
        return int(tok, 0)
    except ValueError:
        raise ValueError(f"'{tok}' is not a number") from None


# ── encoders ─────────────────────────────────────────────────────────────────

def _reg(rA, rB, op4):
    _check_reg(rA); _check_reg(rB)
    return (rA << 6) | (rB << 4) | op4

def _shift(rA, amount, left):
    _check_reg(rA)
    if not 0 <= amount <= 3:
        raise ValueError(f"shift amount {amount} does not fit in 2 bits. "
                         f"SimProc shifts by 0, 1, 2 or 3 — to shift by 4, "
                         f"use two instructions.")
    return (rA << 6) | ((1 if left else 0) << 5) | (amount << 3) | 0b011

def _branch(op4, disp):
    if not -8 <= disp <= 7:
        raise ValueError(f"branch displacement {disp:+d} does not fit in 4 signed "
                         f"bits. SimProc branches reach -8..+7.")
    return ((disp & 0xF) << 4) | op4

def _check_reg(r):
    if r not in (0, 1, 2, 3):
        raise ValueError(f"r{r} does not exist. SimProc has r0, r1, r2, r3.")


# ── disassembly ──────────────────────────────────────────────────────────────

def disasm(word):
    """Turn one byte back into text.  Use this in your failure messages.

    'expected 0x14, got 0x24' tells a student nothing.  'at PC 6, the core ran
    ORI 4 and the model ran ADD r0, r1' tells them where to look."""
    w = word & 0xFF
    op4, op3 = w & 0xF, w & 0x7
    rA, rB = (w >> 6) & 3, (w >> 4) & 3
    disp = ((w >> 4) & 0xF)
    disp = disp - 16 if disp >= 8 else disp
    if op3 == 0b011:                      # SHIFT, both aliases (0x?3 and 0x?B)
        amt = (w >> 3) & 3
        return f"{'SHL' if (w >> 5) & 1 else 'SHR'}   r{rA}, {amt}"
    if op3 == 0b111:                      # ORI, both aliases (0x?7 and 0x?F)
        return f"ORI   {(w >> 3) & 0x1F}"
    return {
        0b0000: f"LOAD  r{rA}, r{rB}",
        0b0010: f"STORE r{rA}, r{rB}",
        0b0100: f"ADD   r{rA}, r{rB}",
        0b0110: f"SUB   r{rA}, r{rB}",
        0b1000: f"NAND  r{rA}, r{rB}",
        0b0001: f"JMP   {disp:+d}",
        0b0101: f"BPZ   {disp:+d}",
        0b1001: f"BNZ   {disp:+d}",
        0b1010: f"BZ    {disp:+d}",
    }.get(op4, "(unimplemented)")


def listing(prog, base=0):
    """A printable address/hex/mnemonic listing.  Put this in a log line when a
    test fails and you will save yourself twenty minutes."""
    return "\n".join(f"  {base + i:02X}: {w:02X}   {disasm(w)}"
                     for i, w in enumerate(prog))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for tok in sys.argv[1:]:
            w = int(tok, 0)
            print(f"0x{w & 0xFF:02X}   {disasm(w)}")
    else:
        print("DD104 — the SimProc assembler.\n")
        print("As a command line tool it disassembles bytes:\n")
        print("    python3 simproc_asm.py 0x2F 0x44 0xD9")
        print("    0x2F   ORI   5")
        print("    0x44   ADD   r1, r0")
        print("    0xD9   BNZ   -3\n")
        print("As a module it assembles them. See the docstring at the top of "
              "this file\nfor the instruction set and the four things about it "
              "that will bite you.")
