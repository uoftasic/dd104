"""Golden ISA model for SimProc, written from src/simproc_system.sv."""

ADD_, SUB_, NAND_ = 0b0100, 0b0110, 0b1000
LOAD_, STORE_ = 0b0000, 0b0010
BNZ_, BPZ_, BZ_, JUMP_ = 0b1001, 0b0101, 0b1010, 0b0001
MEM_DEPTH = 64


class Golden:
    def __init__(self, mem):
        self.mem = list(mem)
        self.rf = [0, 0, 0, 0]
        self.pc = 0
        self.n = 0
        self.z = 0

    def state(self):
        return (tuple(self.rf), self.pc, self.n, self.z)

    def _flags(self, r):
        self.n = (r >> 7) & 1
        self.z = int(r == 0)

    def step(self):
        """Returns cycle count, or a string reason for stopping."""
        if self.pc >= MEM_DEPTH:
            return "PC out of range"
        instr = self.mem[self.pc]
        self.pc = (self.pc + 1) & 0xFF
        op4, op3 = instr & 0xF, instr & 0x7
        ra, rb = (instr >> 6) & 3, (instr >> 4) & 3

        if op4 in (ADD_, SUB_, NAND_):
            a, b = self.rf[ra], self.rf[rb]
            r = {ADD_: (a + b) & 0xFF,
                 SUB_: (a - b) & 0xFF,
                 NAND_: (~(a & b)) & 0xFF}[op4]
            self._flags(r); self.rf[ra] = r
            return 4
        if op3 == 0b011:                      # SHIFT
            amt = (instr >> 3) & 3
            a = self.rf[ra]
            r = ((a << amt) & 0xFF) if (instr >> 5) & 1 else (a >> amt) & 0xFF
            self._flags(r); self.rf[ra] = r
            return 4
        if op4 == LOAD_:
            addr = self.rf[rb]
            if addr >= MEM_DEPTH:
                return "LOAD from address >= 64 (reads X)"
            self.rf[ra] = self.mem[addr]
            return 4
        if op4 == STORE_:
            addr = self.rf[rb]
            if addr < MEM_DEPTH:
                self.mem[addr] = self.rf[ra]
            return 3
        if op4 in (BNZ_, BPZ_, BZ_, JUMP_):
            take = {BNZ_: not self.z, BPZ_: not self.n,
                    BZ_: bool(self.z), JUMP_: True}[op4]
            off = (instr >> 4) & 0xF
            off = off - 16 if off >= 8 else off
            if take:
                self.pc = (self.pc + off) & 0xFF
            return 3
        if op3 == 0b111:                      # ORI  (implicit register R0)
            imm = (instr >> 3) & 0x1F
            r = (self.rf[0] | imm) & 0xFF
            self._flags(r); self.rf[0] = r
            return 5
        return 3                              # illegal opcode: 3 cycles, no state change
