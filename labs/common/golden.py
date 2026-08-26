"""
DD104 — the golden model: SimProc's instruction set, in plain Python.

A *golden model* (or reference model) is a second implementation of the same
specification, written in a language where you can see what it does.  You run
the real design and the model on the same program and compare them after every
instruction.  When they disagree, one of them is wrong — and the interesting
part of verification is that it is not always the hardware.

Why bother, when you could just write `assert sp.reg(1) == 5`?

  * A directed assert checks the one thing you thought of.  A model checks
    everything, every instruction, including the things you did not think of.
    Registers you were not looking at.  Flags.  The PC.
  * It lets you run *random* programs.  You cannot hand-compute the expected
    answer for 30 random instructions, but the model can.
  * It fails with a location.  "instruction 6 disagreed" beats "the final
    answer was wrong" by about half an hour.

And the honest limitation, which DD104 makes you meet in Lab 1: **a model only
checks what it models.**  This one has no concept of `done`, `halt`, cycle
counts or the UART.  A bug in any of those is invisible to it — not because the
model is bad, but because those are not the same kind of property.  You need a
different kind of test, and the course gives you two.

This file imports nothing.  Run it directly (`python3 golden.py`) to execute a
small demo program and print a trace.
"""

MEM_DEPTH = 64

# Opcodes, spelled out.  See simproc_asm.py for the full encoding table.
OP_LOAD, OP_JMP, OP_STORE = 0b0000, 0b0001, 0b0010
OP_ADD, OP_BPZ, OP_SUB = 0b0100, 0b0101, 0b0110
OP_NAND, OP_BNZ, OP_BZ = 0b1000, 0b1001, 0b1010
OP3_SHIFT, OP3_ORI = 0b011, 0b111        # these two are selected by 3 bits, not 4


class Golden:
    """A SimProc that runs in Python.

        g = Golden(program)
        while True:
            r = g.step()
            if isinstance(r, str):    # a string means "I stopped, and here is why"
                break
    """

    def __init__(self, memory, pc=0):
        # Pad to a full 64 bytes with 0x0C, the same unimplemented-opcode
        # filler `SimProc.start()` writes, so the model and the DUT see the
        # same memory even past the end of the program.
        self.mem = [0x0C] * MEM_DEPTH
        for i, v in enumerate(memory):
            self.mem[i] = v & 0xFF
        self.regs = [0, 0, 0, 0]
        self.pc = pc
        self.n = 0
        self.z = 0

    def snapshot(self):
        """(regs, pc, N, Z) — the same shape `SimProc.snapshot()` returns, so
        the two can be compared with `==` and nothing else."""
        return (tuple(self.regs), self.pc, self.n, self.z)

    def _set_flags(self, result):
        """N is the top bit; Z is 'the whole byte was zero'.

        There is no carry flag and no overflow flag in this machine.  8-bit
        arithmetic simply wraps, and nothing tells you it did."""
        self.n = (result >> 7) & 1
        self.z = 1 if result == 0 else 0

    def step(self):
        """Execute one instruction.

        Returns the number of clock cycles the hardware takes for it, or a
        STRING if the model cannot continue.  Returning a reason instead of
        raising means the caller can print it next to the DUT's state."""
        if self.pc >= MEM_DEPTH:
            return (f"PC ran to {self.pc}, past the end of the 64-byte RAM. "
                    f"The hardware reads X here.")

        instr = self.mem[self.pc]
        self.pc = (self.pc + 1) & 0xFF          # the PC increments during FETCH,
                                                # BEFORE a branch computes its
                                                # target — that is why branch
                                                # displacements are measured from
                                                # the following instruction.
        op4 = instr & 0xF
        op3 = instr & 0x7
        rA = (instr >> 6) & 3
        rB = (instr >> 4) & 3

        # ── the two three-bit opcodes come first, because their low nibbles
        #    (0xB and 0xF) would otherwise fall through to the 4-bit table ──
        if op3 == OP3_SHIFT:
            amount = (instr >> 3) & 3           # TWO bits.  0..3, never more.
            left = (instr >> 5) & 1
            value = self.regs[rA]
            result = ((value << amount) & 0xFF) if left else (value >> amount) & 0xFF
            self._set_flags(result)
            self.regs[rA] = result
            return 4

        if op3 == OP3_ORI:
            imm = (instr >> 3) & 0x1F           # FIVE bits of immediate
            result = (self.regs[0] | imm) & 0xFF
            self._set_flags(result)
            self.regs[0] = result               # ORI always writes r0
            return 5

        # ── the four-bit opcodes ──
        if op4 in (OP_ADD, OP_SUB, OP_NAND):
            a, b = self.regs[rA], self.regs[rB]
            result = {OP_ADD: (a + b) & 0xFF,
                      OP_SUB: (a - b) & 0xFF,
                      OP_NAND: (~(a & b)) & 0xFF}[op4]
            self._set_flags(result)
            self.regs[rA] = result
            return 4

        if op4 == OP_LOAD:
            addr = self.regs[rB]                # rB is the pointer
            if addr >= MEM_DEPTH:
                return (f"LOAD from address {addr}, past the end of the 64-byte "
                        f"RAM. The hardware reads X here.")
            self.regs[rA] = self.mem[addr]
            return 4

        if op4 == OP_STORE:
            addr = self.regs[rB]
            if addr < MEM_DEPTH:
                self.mem[addr] = self.regs[rA]
            # else: the hardware silently drops it, and so do we.  Verified:
            # writing to 0x45 does not alias down into 0x05.
            return 3

        if op4 in (OP_JMP, OP_BPZ, OP_BNZ, OP_BZ):
            taken = {OP_JMP: True,
                     OP_BPZ: self.n == 0,
                     OP_BNZ: self.z == 0,
                     OP_BZ: self.z == 1}[op4]
            disp = (instr >> 4) & 0xF
            disp = disp - 16 if disp >= 8 else disp     # 4-bit SIGNED
            if taken:
                self.pc = (self.pc + disp) & 0xFF
            # Branches do NOT touch the flags.  That is deliberate: it lets you
            # compare once and branch on the result twice.
            return 3

        # Opcodes 0xC, 0xD, 0xE are not implemented.  The hardware moves the PC
        # on, changes nothing else, and never pulses `done` — which the model
        # has no way to represent.
        #
        # FOUR cycles, not three, and the extra one is not decoration.  Every
        # other instruction leaves CYCLE_3 or CYCLE_4 straight back to CYCLE_1;
        # an unimplemented opcode matches no clause in CYCLE_3, so the FSM takes
        # its default exit to IDLE and needs one more cycle to be sent out of it
        # again.  `halt` is therefore HIGH for one cycle in the middle of a
        # free-running program — measured: 4 filler bytes take 16 clocks, with
        # `halt` high on 4 of them and 0 `done` pulses.
        #
        # This model said 3 until somebody measured it.  See
        # docs/guide/the-golden-model.md — it is the course's own worked
        # example of a model being the wrong one of the two.
        return 4

    def run(self, n_instructions, stop_on_reason=True):
        """Step `n_instructions` times.  Returns (cycles, reason_or_None)."""
        cycles = 0
        for _ in range(n_instructions):
            r = self.step()
            if isinstance(r, str):
                return cycles, (r if stop_on_reason else None)
            cycles += r
        return cycles, None

    def memory(self, lo=0, hi=MEM_DEPTH):
        return {a: self.mem[a] for a in range(lo, hi)}


def compare_memory(model, sp, lo=0, hi=MEM_DEPTH):
    """Every address where the model and the DUT disagree.

    Returns a list of (address, model_value, dut_value).  An empty list is the
    good answer."""
    out = []
    for a in range(lo, hi):
        want = model.mem[a]
        try:
            got = sp.peek(a)
        except ValueError:
            got = None                     # X in RAM — worth reporting as-is
        if got != want:
            out.append((a, want, got))
    return out


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from simproc_asm import assemble, listing

    # Sum 1+2+3+4+5 and store the answer at 0x20.
    #
    # Note the two `SUB r0, r0` before each `ORI`: ORI only ever SETS bits, so
    # you have to clear the register first or you get the OR of everything you
    # have ever put there.  That is the single most common way to write a
    # SimProc program that is wrong and looks right.
    prog = assemble("""
            SUB   r0, r0        # r0 = 0
            ORI   1             # r0 = 1
            SUB   r2, r2
            ADD   r2, r0        # r2 = 1        the amount we count down by
            SUB   r0, r0
            ORI   5             # r0 = 5        the counter
            SUB   r1, r1        # r1 = 0        the running total
    loop:   ADD   r1, r0        #   total += counter
            SUB   r0, r2        #   counter -= 1
            BNZ   loop          #   ... until the counter hits zero
            SUB   r0, r0
            ORI   4
            SHL   r0, 3         # r0 = 32 = 0x20
            SUB   r3, r3
            ADD   r3, r0        # r3 = 0x20     where the answer goes
            STORE r1, r3        # mem[0x20] = total
    """)
    print(listing(prog))
    # 7 instructions of setup, a 3-instruction loop body five times over,
    # then 6 more.  7 + 15 + 6 = 28 instructions executed, and the cycle count
    # is a number you can add up by hand from the table in simproc_asm.py:
    #   setup   4+5+4+4+4+5+4                        = 30
    #   loop    (ADD 4 + SUB 4 + BNZ 3) x 5          = 55
    #   finish  4+5+4+4+4 + STORE 3                  = 24
    EXECUTED = 28
    g = Golden(prog)
    cycles, reason = g.run(EXECUTED)
    print(f"\n{len(prog)} instructions in memory, {EXECUTED} executed, "
          f"{cycles} clock cycles")
    print(f"registers: r0={g.regs[0]} r1={g.regs[1]} r2={g.regs[2]} r3={g.regs[3]}")
    print(f"mem[0x20] = {g.mem[0x20]}   ({reason or f'all {EXECUTED} instructions executed'})")
