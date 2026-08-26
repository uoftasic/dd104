"""SimProc host-side model: assembler + UART bus-functional model (cocotb 2.x)."""
import cocotb
from cocotb.triggers import ClockCycles, RisingEdge, Timer, First

# ---------------- Assembler ----------------
# Instruction word is 8 bits, [7:0].
def ADD(a, b):   return (a << 6) | (b << 4) | 0b0100
def SUB(a, b):   return (a << 6) | (b << 4) | 0b0110
def NAND(a, b):  return (a << 6) | (b << 4) | 0b1000
def LOAD(a, b):  return (a << 6) | (b << 4) | 0b0000
def STORE(a, b): return (a << 6) | (b << 4) | 0b0010
def ORI(imm5):   return ((imm5 & 0x1F) << 3) | 0b111
def SHL(a, amt): return (a << 6) | (1 << 5) | ((amt & 3) << 3) | 0b011
def SHR(a, amt): return (a << 6) | (0 << 5) | ((amt & 3) << 3) | 0b011
def _br(op, off): return ((off & 0xF) << 4) | op
def BNZ(off):    return _br(0b1001, off)
def BPZ(off):    return _br(0b0101, off)
def BZ(off):     return _br(0b1010, off)
def JMP(off):    return _br(0b0001, off)
def ILLEGAL():   return 0b1100

# ---------------- UART command bytes ----------------
CMD_READ, CMD_WRITE, CMD_PING = 0xA3, 0x5C, 0xF0
CMD_RUN, CMD_HALT, CMD_STEP   = 0x3F, 0xC7, 0x6D
CMD_SET_PC, CMD_GET_PC        = 0x99, 0xB2


class SimProcBus:
    """Drives ui_in[0] / samples uo_out[0] as a UART at clk_per_bit = 4*uio."""

    def __init__(self, dut, uio=2):
        self.dut = dut
        self.uio = uio
        self.cpb = uio * 4          # clk_per_bit as the wrapper builds it

    async def reset(self):
        d = self.dut
        d.ena.value = 1
        d.ui_in.value = 1           # UART idle is high
        d.uio_in.value = self.uio
        d.rst_n.value = 0
        await ClockCycles(d.clk, 10)
        d.rst_n.value = 1
        await ClockCycles(d.clk, 4)

    async def _send_byte(self, val):
        d = self.dut
        bits = [0] + [(val >> i) & 1 for i in range(8)] + [1]
        for b in bits:
            d.ui_in.value = b
            await ClockCycles(d.clk, self.cpb)
        d.ui_in.value = 1
        await ClockCycles(d.clk, self.cpb)   # inter-frame gap

    async def _recv_byte(self, timeout_cycles=4000):
        """Sample uo_out[0] as a UART receiver."""
        d = self.dut
        for _ in range(timeout_cycles):
            await RisingEdge(d.clk)
            if (int(d.uo_out.value) & 1) == 0:
                break
        else:
            raise TimeoutError("no UART start bit on uo_out[0]")
        # centre of the start bit, then step a bit period at a time
        await ClockCycles(d.clk, self.cpb // 2)
        val = 0
        for i in range(8):
            await ClockCycles(d.clk, self.cpb)
            val |= (int(d.uo_out.value) & 1) << i
        await ClockCycles(d.clk, self.cpb)   # stop bit
        return val

    async def cmd(self, c, addr=0, data=0):
        await self._send_byte(c)
        await self._send_byte(addr)
        await self._send_byte(data)
        await ClockCycles(self.dut.clk, 8)

    async def stop(self):
        """Stop the core now, without waiting out a three-byte UART command.

        A HALT command takes 33 bit-times to shift in -- 1,056 clocks at
        clk_per_bit = 32 -- and the core keeps executing the whole time.  Past
        the end of a short program it walks through unimplemented opcodes at 3
        cycles each, and the PC is 8 bits wide against a 64-byte RAM, so it
        wraps to 0 and runs the program a second time.  That corrupts memory
        before a scoreboard can read it.  Pulsing rst_n stops it in 6 clocks;
        the RAM has no reset, so the program and its results survive.
        """
        d = self.dut
        d.rst_n.value = 0
        await ClockCycles(d.clk, 4)
        d.rst_n.value = 1
        await ClockCycles(d.clk, 2)

    async def write(self, addr, data): await self.cmd(CMD_WRITE, addr, data)
    async def set_pc(self, addr):      await self.cmd(CMD_SET_PC, addr, 0)
    async def run(self):               await self.cmd(CMD_RUN)
    async def halt(self):              await self.cmd(CMD_HALT)

    async def step(self):
        """One instruction. STEP pulses run for one cycle."""
        await self.cmd(CMD_STEP)

    async def read(self, addr):
        await self._send_byte(CMD_READ)
        await self._send_byte(addr)
        await self._send_byte(0)
        return await self._recv_byte()

    async def ping(self):
        await self._send_byte(CMD_PING); await self._send_byte(0); await self._send_byte(0)
        return await self._recv_byte()

    async def get_pc(self):
        await self._send_byte(CMD_GET_PC); await self._send_byte(0); await self._send_byte(0)
        return await self._recv_byte()

    async def load_program(self, prog, base=0):
        for i, w in enumerate(prog):
            await self.write(base + i, w)

    # ---- white-box probes (Icarus hierarchical access) ----
    def rf(self, i):   return int(self.dut.tt_um_ieeeuoftasic_simproc.U1.CPU1.RF1.rf[i].value)
    def pc(self):      return int(self.dut.tt_um_ieeeuoftasic_simproc.U1.CPU1.PC1.pc_out.value)
    def mem(self, a):  return int(self.dut.tt_um_ieeeuoftasic_simproc.U1.RAM1.mem[a].value)
    def flags(self):
        c = self.dut.tt_um_ieeeuoftasic_simproc.U1.CPU1
        return int(c.n_flag_out.value), int(c.z_flag_out.value)


STATE_NAMES = ["IDLE", "CYCLE_1", "CYCLE_2", "CYCLE_3", "CYCLE_4", "CYCLE_5", "?6", "?7"]


class StateMonitor:
    """Samples the core FSM state every rising clock edge."""

    def __init__(self, dut):
        self.dut = dut
        self.core = dut.tt_um_ieeeuoftasic_simproc.U1.CPU1
        self.trace = []
        self._task = None

    def start(self):
        self.trace = []
        self._task = cocotb.start_soon(self._run())

    async def _run(self):
        while True:
            await RisingEdge(self.dut.clk)
            try:
                s = int(self.core.curr_state.value)
            except Exception:
                s = -1
            self.trace.append(s)

    def stop(self):
        if self._task:
            self._task.cancel()

    def instr_windows(self):
        """Return list of state sequences between IDLE runs."""
        out, cur = [], []
        for s in self.trace:
            if s == 0:
                if cur:
                    out.append(cur); cur = []
            else:
                cur.append(s)
        if cur:
            out.append(cur)
        return out
