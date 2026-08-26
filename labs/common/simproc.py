"""
DD104 — the SimProc test harness.

This is the file every DD104 lab imports.  It gives you a `SimProc` object
that knows how to start the chip, get a program into it, run it, and read the
answer back out.  A whole test looks like this:

    import cocotb
    from simproc import SimProc
    from simproc_asm import *

    @cocotb.test()
    async def r1_gets_five(dut):
        sp = SimProc(dut)
        await sp.start()                          # clock, reset, blank memory
        cycles = await sp.run([ORI(5), ADD(1, 0)])   # r0 = 5 ; r1 = r1 + r0
        assert sp.reg(1) == 5, f"r1 is {sp.reg(1)}, expected 5"
        assert cycles == 9, f"took {cycles} cycles, expected 5 + 4"

Read this file.  It is the worked example for everything the labs ask you to
write, and it is deliberately longer on comments than on code.

────────────────────────────────────────────────────────────────────────────
COCOTB 2.x — READ THIS BEFORE YOU SEARCH THE INTERNET
────────────────────────────────────────────────────────────────────────────
The workbench has **cocotb 2.0.1**.  Almost every cocotb tutorial you will
find online was written for 1.x.  Some 1.x code still runs here and some of it
stops dead, and the split is not where you would guess — so here is what each
one actually does in this image, measured, not remembered.

**Renamed, but still works, with a warning.**  These will not break your test.
They will fill your log with noise and stop working at some future version:

    Timer(1, units="ns")     ->  DeprecationWarning:
    Clock(clk, 10, units=…)      "The 'units' argument has been renamed to 'unit'."
                                 Write `unit`, singular.

    MODULE=my_test           ->  "Using MODULE is deprecated, please use
      (in a Makefile)             COCOTB_TEST_MODULES instead."
                                 Write COCOTB_TEST_MODULES. sim.mk does.

**Gone.  These stop your test with an error that does not mention cocotb.**

    cocotb.fork(coro)        ->  AttributeError: module 'cocotb' has no
                                 attribute 'fork'
                                 Use `cocotb.start_soon(coro)`.

    @cocotb.coroutine        ->  AttributeError: module 'cocotb' has no
                                 attribute 'coroutine'
                                 Use `async def` and `await`.

    dut.sig <= 1             ->  TypeError: '<=' not supported between
                                 instances of 'LogicArrayObject' and 'int'
                                 Use `dut.sig.value = 1`.  In 1.x `<=` was an
                                 assignment operator; it was always a Python
                                 comparison wearing a costume.

**Unchanged, whatever the migration guides imply.**  `.value.integer`,
`.value.binstr` and `.value.buff` all still work, and `TestFactory` still
imports.

**And one that is new.**  In 2.x, `int()` on a signal that contains an X or a
Z raises instead of guessing:

    ValueError: Can't convert LogicArray to int: it contains non-0/1 values

That is a feature.  It means an undefined value cannot silently become a
number in your comparison.  See `bit()` below for how to look at such a signal
on purpose.

**Two things that look like they should run this file and do not.**

    python3 -m pytest test_example.py   ->  "collected 0 items"
                                            "no tests ran in 0.10s"   exit 0
    python3 test_example.py             ->  no output at all          exit 0

Both are green, both did nothing, and neither says so.  A cocotb test is not a
Python program and not a pytest test — it needs a simulator underneath it, and
the only thing that starts one here is `make`.

────────────────────────────────────────────────────────────────────────────
THE CHIP, IN ONE SCREEN
────────────────────────────────────────────────────────────────────────────
SimProc is an 8-bit processor with 4 registers and 64 bytes of RAM, wrapped in
a TinyTapeout pin frame.  From outside, all it has is:

    ui_in[0]   -> uart_rx     one serial input pin.  Everything goes in here.
    uo_out[0]  <- uart_tx     one serial output pin.  Everything comes out here.
    uo_out[1]  <- halt        1 when the core is sitting in IDLE
    uo_out[2]  <- done        pulses high for one cycle per retired instruction
    uio_in[7:0]               the baud divider: clk_per_bit = uio_in * 4
    rst_n                     ACTIVE LOW

The only way in from the outside is a 3-byte UART command — always three
bytes, `cmd addr data`, even when addr and data are ignored:

    0xA3 READ    replies with mem[addr]        0x5C WRITE   mem[addr] = data
    0xF0 PING    replies 0xAA                  0x3F RUN     start free-running
    0xC7 HALT    stop                          0x6D STEP    exactly one instruction
    0x99 SET_PC  PC = addr (only in IDLE)      0xB2 GET_PC  replies with the PC

At the default baud one command costs exactly 1104 clock cycles (measured), so
loading a 64-byte program over the wire costs 70,656 — which is why this
harness also has a **memory backdoor** (`poke`/`peek`/`load`) that reaches into
the RAM array directly.  Both are here, both are honest, and §"The backdoor" below says
when to use which.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

from simproc_asm import JMP, UNIMP, disasm


# ── UART command bytes ───────────────────────────────────────────────────────
CMD_READ   = 0xA3
CMD_WRITE  = 0x5C
CMD_PING   = 0xF0
CMD_RUN    = 0x3F
CMD_HALT   = 0xC7
CMD_STEP   = 0x6D
CMD_SET_PC = 0x99
CMD_GET_PC = 0xB2

PING_REPLY = 0xAA

# The core's FSM states, so a failure message can say CYCLE_3 and not "3".
STATE_NAMES = ["IDLE", "CYCLE_1", "CYCLE_2", "CYCLE_3", "CYCLE_4", "CYCLE_5", "?6", "?7"]

MEM_DEPTH = 64          # dp_ram is 64 bytes.  Addresses 64..255 read X.

FILLER = UNIMP()        # 0x0C: an unimplemented opcode. Four cycles, PC+1,
                        # nothing else, and no `done` pulse — but `halt` does
                        # blip high for one of the four. See simproc_asm.UNIMP.
PARK = JMP(-1)          # 0xF1: a jump to itself. The idiom for "the program is
                        # over" on a machine with no HALT instruction.


def bit(signal, index):
    """One bit of a signal, as the character '0', '1', 'x' or 'z'.

    Use this instead of `(int(sig.value) >> i) & 1` on anything a broken design
    might drive to X.  `int()` on a LogicArray containing X raises ValueError
    in cocotb 2.x, and a test that dies with

        ValueError: Can't convert LogicArray to int: it contains non-0/1 values

    has told you something real — an X reached the pin — but it has told you
    with a stack trace instead of an assertion, which is a worse way to find
    out.  Reading the bit as a character lets you say so on purpose."""
    return str(signal.value[index])


class SimProc:
    """A running SimProc, with a UART attached and a backdoor into its RAM."""

    # ── setup ────────────────────────────────────────────────────────────────

    def __init__(self, dut, clock_ns=10, uio=8):
        """`uio` sets the baud rate: clk_per_bit = uio * 4.

        The default of 8 gives clk_per_bit = 32.  That is fast enough that
        tests finish, and slow enough that the UART is comfortably inside spec.
        Some labs will ask you to change it — a parameter that is only ever
        tested at its default value is a parameter that is only tested once."""
        self.dut = dut
        self.clock_ns = clock_ns
        self.uio = uio
        self.clk_per_bit = uio * 4

        # Hierarchical handles.  These reach *inside* the design, past the pins.
        # A real chip has no such thing; a simulation does, and refusing to use
        # it out of purity costs you an afternoon per bug.
        self.chip = dut.tt_um_ieeeuoftasic_simproc   # the TinyTapeout wrapper
        self.sys = self.chip.U1                      # simproc_system
        self.cpu = self.sys.CPU1                     # the core
        self.ram = self.sys.RAM1.mem                 # the 64-byte array
        self.rf = self.cpu.RF1.rf                    # the 4 registers

        self._park = None       # address of the parking loop, set by load()
        self._rx = []           # bytes the chip has sent, as bit strings
        self._rx_task = None

    async def start(self, fill=FILLER):
        """Start the clock, reset the chip, blank the RAM, and start listening.

        `fill` is what unwritten memory gets.  The default is 0x0C, an
        unimplemented opcode: four cycles, PC+1, no state change.  So if your
        program runs off its own end, the core walks harmlessly through filler
        instead of executing whatever happened to be lying in memory.

        Without the fill, unwritten RAM in Icarus reads `XXXXXXXX`, the core
        decodes X, and you get a hang with no error message at all."""
        cocotb.start_soon(Clock(self.dut.clk, self.clock_ns, unit="ns").start())
        await self.reset()
        for a in range(MEM_DEPTH):
            self.ram[a].value = fill
        self._start_uart_monitor()
        await ClockCycles(self.dut.clk, 2)

    async def reset(self):
        """Pulse rst_n low for 10 cycles.

        This clears the registers, the PC and the flags — and **not the RAM**.
        `dp_ram` has no reset, so whatever you loaded survives.  That is what
        lets you load a program, reset the core, and run from a known state."""
        d = self.dut
        d.ena.value = 1
        d.ui_in.value = 1           # a UART line at rest sits HIGH
        d.uio_in.value = self.uio
        d.rst_n.value = 0           # ACTIVE LOW
        await ClockCycles(d.clk, 10)
        d.rst_n.value = 1
        await ClockCycles(d.clk, 4)
        self._rx.clear()        # anything the TX pin did during reset is noise

    async def set_baud(self, uio):
        """Change the baud divider mid-test: clk_per_bit becomes uio * 4.

        The chip reads `clk_per_bit` straight off uio_in every cycle, so this
        takes effect immediately.  The harness's own receiver reads
        `self.clk_per_bit` each time it decodes a frame, so it follows along.

        A parametric design that is only ever tested at its default parameter
        has been tested at one point of a range."""
        self.uio = uio
        self.clk_per_bit = uio * 4
        self.dut.uio_in.value = uio
        self._rx.clear()
        await ClockCycles(self.dut.clk, 4)

    # ── the backdoor ─────────────────────────────────────────────────────────
    #
    # `poke`/`peek`/`load` write and read the RAM array directly, in zero
    # simulated time.  The UART path (`uart_write`, `uart_read`) does the same
    # job through the actual pins, 1104 clock cycles per command.
    #
    # Use the backdoor for setup — getting a program in, checking a result.
    # Use the UART when the UART is what you are testing.  Every lab in this
    # course does the first; Lab 5 does the second, and finds a bug that the
    # backdoor structurally cannot see.

    def poke(self, addr, value):
        """Write one byte of RAM directly."""
        self._check_addr(addr)
        self.ram[addr].value = value & 0xFF

    def peek(self, addr):
        """Read one byte of RAM directly.  Returns an int, or raises if X."""
        self._check_addr(addr)
        return int(self.ram[addr].value)

    async def load(self, program, at=0, park=True):
        """Put a list of instruction bytes into memory starting at `at`.

        Unless you say `park=False`, this also writes one `JMP -1` immediately
        after the last instruction.  That is a jump to itself: when the core
        reaches it, it spins there and the machine's state stops changing.

        You need it because of how HALT works.  There is no way to stop this
        processor after exactly N instructions — HALT arrives over the UART and
        takes 1104 clock cycles to get there, and the core runs the whole
        time.  A program that parks itself is how real bare-metal test code
        solves the same problem, and it is what lets `run()` return an exact
        cycle count.

        Takes 2 clock cycles, to let the RAM's combinational read ports settle.
        Does not reset the core and does not start it."""
        for i, word in enumerate(program):
            self.poke(at + i, word)
        self._park = None
        if park:
            self._park = at + len(program)
            self.poke(self._park, PARK)
        await ClockCycles(self.dut.clk, 2)
        return self._park

    def _check_addr(self, addr):
        if not 0 <= addr < MEM_DEPTH:
            raise IndexError(
                f"address {addr} (0x{addr:02X}) is outside SimProc's {MEM_DEPTH}-byte "
                f"RAM. The hardware addresses it with 8 bits but only has 64 entries, "
                f"so on real silicon this read returns X and this write is dropped. "
                f"Verilator's linter says so statically; Icarus only shows it at "
                f"run time. See Lab 2.")

    # ── reading the machine ──────────────────────────────────────────────────

    def reg(self, i):
        """Register r0..r3, as an int."""
        return int(self.rf[i].value)

    def regs(self):
        """All four registers as a tuple — the thing to put in a failure message."""
        return tuple(self.reg(i) for i in range(4))

    def pc(self):
        """The program counter."""
        return int(self.cpu.PC1.pc_out.value)

    def flags(self):
        """(N, Z).  N is bit 7 of the last flag-setting result; Z is 'it was 0'.

        Only ADD, SUB, NAND, SHIFT and ORI write these.  LOAD, STORE and every
        branch leave them alone, on purpose."""
        return int(self.cpu.n_flag_out.value), int(self.cpu.z_flag_out.value)

    def fsm(self):
        """The core's current state, as a name: IDLE, CYCLE_1 ... CYCLE_5."""
        return STATE_NAMES[int(self.cpu.curr_state.value)]

    @property
    def halt(self):
        """The halt PIN (uo_out[1]): 1 while the core sits in IDLE."""
        return bit(self.dut.uo_out, 1)

    @property
    def done(self):
        """The done PIN (uo_out[2]): one cycle high per retired instruction."""
        return bit(self.dut.uo_out, 2)

    def snapshot(self):
        """Everything a program can change, in one tuple: (regs, pc, N, Z).

        Comparing snapshots is how you compare a real core against a model
        without writing four asserts every time."""
        n, z = self.flags()
        return (self.regs(), self.pc(), n, z)

    def describe(self):
        """A one-line human-readable state dump for failure messages."""
        r = self.regs()
        n, z = self.flags()
        return (f"PC={self.pc():2d}  r0={r[0]:3d} r1={r[1]:3d} r2={r[2]:3d} "
                f"r3={r[3]:3d}  N={n} Z={z}  {self.fsm()}")

    def memory(self, lo=0, hi=MEM_DEPTH):
        """A dict of RAM contents, for dumping when a test fails.

        Bytes that contain an X come back as the string `'XXXXXXXX'` rather
        than raising — a dump you print because something already went wrong
        should not itself blow up on the interesting entry."""
        out = {}
        for a in range(lo, hi):
            try:
                out[a] = self.peek(a)
            except ValueError:
                out[a] = str(self.ram[a].value)
        return out

    # ── making it go ─────────────────────────────────────────────────────────
    #
    # SimProc has exactly two ways to execute anything, and they are not
    # interchangeable:
    #
    #   RUN   free-runs until you send HALT.  Fast.  But HALT arrives over the
    #         UART, which takes 1104 clock cycles to transmit — during which
    #         the core keeps going.  So you CANNOT stop after exactly N
    #         instructions this way.  Nothing can; the hardware has no such
    #         button.
    #   STEP  executes exactly one instruction and drops back to IDLE.  Exact,
    #         and costs a whole UART command per instruction.
    #
    # `run()` deals with the first problem the way real bare-metal test
    # programs do: it puts an infinite loop on the end of your program.  The
    # core reaches it, spins there harmlessly, and the state you wanted to look
    # at stops changing.  Then HALT can take as long as it likes.

    async def run(self, program=None, at=0, timeout_cycles=20000):
        """Load `program`, run it to the end, and return how many clock cycles
        it took.

        This is the call you will use most.  It appends a parking loop
        (`JMP -1`, one byte) after the last instruction, starts the core, and
        watches the fetch address until it arrives there.

        The returned cycle count is exact and hand-checkable: it is the number
        of clocks between fetching the first instruction and fetching the
        parking loop, which is the sum of your program's instruction times and
        nothing else.  ORI 5, ADD/SUB/NAND/SHIFT/LOAD 4, STORE and branches 3.

        Pass `program=None` to run something you loaded earlier with `load()`."""
        if program is not None:
            await self.load(program, at=at)
        if self._park is None:
            raise ValueError("run() needs a program with a parking loop. Either "
                             "pass one in, or call load(prog) first.")
        await self.set_pc(at)
        return await self._run_to_park(timeout_cycles)

    async def _run_to_park(self, timeout_cycles):
        park = self._park
        out = {}

        async def watcher():
            cycles = -1                  # -1 until the first instruction is fetched
            was = self.fsm()
            for _ in range(timeout_cycles):
                await RisingEdge(self.dut.clk)
                if cycles >= 0:
                    cycles += 1
                now = self.fsm()
                fetching = (now == "CYCLE_1" and was != "CYCLE_1")
                was = now
                if not fetching:
                    continue
                if cycles < 0:
                    cycles = 0           # this edge is the first instruction fetch
                if self.pc() == park:
                    out["cycles"] = cycles
                    return

        await self._go(watcher())
        if "cycles" not in out:
            raise TimeoutError(
                f"the program did not reach its parking loop at address {park} "
                f"within {timeout_cycles} clock cycles.\n"
                f"    {self.describe()}\n"
                f"  IDLE means the core never started. A PC far past your program "
                f"means it ran off the end — check your branch displacements. A PC "
                f"that is not moving means an infinite loop you did not intend.")
        return out["cycles"]

    async def _go(self, watcher):
        """Start `watcher` BEFORE sending RUN, then HALT when it is finished.

        The order matters and it is not obvious.  A RUN command takes 1104
        clock cycles to shift in, and the chip acts on it 57 cycles before the
        last stop bit has finished going out — so a monitor started after
        `start_running()` returns has already missed about fourteen
        instructions.  Both numbers are measured, not estimated.  Every
        measurement in this class that counts anything goes through here for
        exactly that reason."""
        task = cocotb.start_soon(watcher)
        await self.start_running()
        await task
        await self.stop_running()
        await self._await_idle()

    async def start_running(self):
        """Send RUN.  The core free-runs until you send HALT."""
        await self.uart_cmd(CMD_RUN)

    async def stop_running(self):
        """Send HALT.  Takes effect when the current instruction retires — and
        the command itself takes 1104 clocks to arrive, during which the core is
        still running."""
        await self.uart_cmd(CMD_HALT)

    async def set_pc(self, addr):
        """Send SET_PC.  Only takes effect while the core is in IDLE."""
        await self.uart_cmd(CMD_SET_PC, addr=addr)

    async def run_cycles(self, n):
        """Run the loaded program for `n` clock cycles of EXECUTION, then halt.

        The count starts at the first instruction fetch, not at the moment the
        RUN command was sent — see `_go`.  Use this when the question is about
        time rather than about the answer: 'after 40 clocks, how far has it
        got?'"""
        async def watcher():
            was = self.fsm()
            started = False
            k = 0
            while k < n:
                await RisingEdge(self.dut.clk)
                now = self.fsm()
                if now == "CYCLE_1" and was != "CYCLE_1":
                    started = True
                was = now
                if started:
                    k += 1
        await self._go(watcher())

    async def step(self, n=1):
        """Execute exactly `n` instructions, one STEP command each.

        STEP pulses `run` for a single cycle: the core executes one
        instruction and falls back into IDLE.  This is the mode to use when
        you want to inspect the machine's state after every single
        instruction — `trace()` at the bottom of this file is built on it."""
        for _ in range(n):
            await self.uart_cmd(CMD_STEP)
            await self._await_idle()

    async def _await_idle(self, max_cycles=64):
        """Wait for the core to come to rest in IDLE."""
        for _ in range(max_cycles):
            if self.fsm() == "IDLE":
                return
            await RisingEdge(self.dut.clk)
        raise TimeoutError(
            f"the core did not come back to IDLE within {max_cycles} clocks of "
            f"being told to stop.\n"
            f"    {self.describe()}\n"
            f"  The longest instruction is 5 cycles, so a core still moving "
            f"after {max_cycles} is stuck — most likely decoding an X, which "
            f"means the PC is somewhere there is no program.")

    async def count_done_pulses(self, cycles):
        """Run the loaded program and count rising edges of `done` over the
        first `cycles` clocks of execution.

        This is a PROTOCOL check, not a data check.  A core can compute every
        right answer and still get its handshake wrong — and if your scoreboard
        is triggered by `done`, a missing pulse does not make your test fail,
        it makes your test quietly stop looking.  Which is worse.

        `done` should pulse once per retired instruction.  Instructions with an
        unimplemented opcode (0xC, 0xD, 0xE) never pulse it, so keep those out
        of a program you are counting."""
        out = {"done": 0, "fetches": 0}

        async def watcher():
            prev_done, was = "0", self.fsm()
            started = False
            n = 0
            while n < cycles:
                await RisingEdge(self.dut.clk)
                now = self.fsm()
                if now == "CYCLE_1" and was != "CYCLE_1":
                    started = True
                    out["fetches"] += 1
                was = now
                if not started:
                    continue
                n += 1
                d = self.done
                if d == "1" and prev_done != "1":
                    out["done"] += 1
                prev_done = d

        await self._go(watcher())
        return out["done"]

    async def count_halt_cycles(self, cycles):
        """Run the loaded program and count how many of the first `cycles`
        clocks of execution had `halt` high.

        While RUN is asserted the answer should be zero.  A core that blips
        back into IDLE between instructions still computes every right answer,
        and is still wrong: on real silicon that is a wasted cycle and a glitch
        a debugger can see."""
        out = {"halt": 0}

        async def watcher():
            was = self.fsm()
            started = False
            n = 0
            while n < cycles:
                await RisingEdge(self.dut.clk)
                now = self.fsm()
                if now == "CYCLE_1" and was != "CYCLE_1":
                    started = True
                was = now
                if not started:
                    continue
                n += 1
                if self.halt == "1":
                    out["halt"] += 1

        await self._go(watcher())
        return out["halt"]

    # ── the UART, one bit at a time ──────────────────────────────────────────
    #
    # This is a bus functional model (BFM): Python that pretends to be the
    # thing on the other end of the wire.  It knows the protocol — 8N1: one low
    # start bit, eight data bits least-significant first, one high stop bit —
    # and nothing else about the design.  If the chip's idea of a bit period
    # drifts from this one, the two stop understanding each other, which is
    # exactly the failure a baud sweep goes looking for.
    #
    # The receiver runs as a BACKGROUND TASK, started by `start()`, watching
    # uo_out[0] from before the first command is sent.  It has to: the chip can
    # begin its reply while the harness is still finishing the last stop bit of
    # the command, and a receiver that only starts looking afterwards misses
    # the beginning of the frame.  When that happens you do not get an error —
    # you get a plausible wrong byte.  A PING that should answer 0xAA comes
    # back 0xD5, which is 0xAA sampled one bit period late.

    def _start_uart_monitor(self):
        self._rx = []
        self._rx_task = cocotb.start_soon(self._uart_monitor())

    async def _uart_monitor(self):
        d = self.dut
        prev = "1"
        while True:
            await RisingEdge(d.clk)
            now = bit(d.uo_out, 0)
            start = (prev == "1" and now == "0")
            prev = now
            if not start:
                continue
            # We are at most one clock into the start bit. Step to its middle,
            # then one full bit period per data bit — sampling in the MIDDLE of
            # each bit, which is what makes a real UART tolerant of a small
            # clock difference at all.
            await ClockCycles(d.clk, self.clk_per_bit // 2)
            chars = []
            for _ in range(8):
                await ClockCycles(d.clk, self.clk_per_bit)
                chars.append(bit(d.uo_out, 0))
            await ClockCycles(d.clk, self.clk_per_bit)      # stop bit
            prev = bit(d.uo_out, 0)
            self._rx.append("".join(reversed(chars)))       # MSB-first string

    async def send_byte(self, value):
        """Bit-bang one byte into ui_in[0], then leave one bit period of idle.

        That trailing idle is not politeness, it is required, and the reason is
        worth knowing because it is the kind of thing that only shows up as a
        wrong answer.  The chip's receiver spends

            (clk_per_bit-1)>>1   cycles finding the middle of the start bit
            9 x clk_per_bit      cycles receiving (8 data bits and the stop bit)
            1 x clk_per_bit      cycles in a DONE state before it looks again

        which is about half a bit period LONGER than the frame it just
        received.  Send the next start bit the instant the stop bit ends and
        the receiver is still in DONE and misses it — then it catches the start
        bit late, samples every bit late, and hands the command FSM a byte that
        is this byte shifted by one.

        You do not get an error.  You get 0x00 arriving as 0x80.  A PING still
        works, because PING ignores its address and data bytes; SET_PC quietly
        sets the program counter to 128."""
        d = self.dut
        frame = [0] + [(value >> i) & 1 for i in range(8)] + [1]   # start, LSB..MSB, stop
        for b in frame:
            d.ui_in.value = b
            await ClockCycles(d.clk, self.clk_per_bit)
        d.ui_in.value = 1                                   # back to idle
        await ClockCycles(d.clk, self.clk_per_bit)          # the gap the RX needs

    async def recv_byte(self, timeout_cycles=20000):
        """Take the next byte the chip sent.  Raises if it never arrives, or if
        what arrived was not eight 0s and 1s."""
        for _ in range(timeout_cycles):
            if self._rx:
                break
            await RisingEdge(self.dut.clk)
        else:
            raise TimeoutError(
                f"the chip sent nothing within {timeout_cycles} clocks.\n"
                f"  READ, PING and GET_PC reply. WRITE, RUN, HALT, STEP and "
                f"SET_PC do not — asking one of those for a reply waits forever.\n"
                f"  Every command is THREE bytes (cmd, addr, data) even when the "
                f"last two are ignored. Send two and the chip is still waiting.")
        bits = self._rx.pop(0)
        if any(c not in "01" for c in bits):
            raise ValueError(
                f"the chip sent '{bits}' — that is not eight 0s and 1s. An X on "
                f"the TX pin means the design drove the pin from something "
                f"undefined. Reading RAM above address 63 does exactly this: the "
                f"array is 64 deep and the address bus is 8 bits wide.")
        return int(bits, 2)

    async def uart_cmd(self, cmd, addr=0, data=0):
        """Send one 3-byte command.  Does not wait for a reply."""
        await self.send_byte(cmd)
        await self.send_byte(addr)
        await self.send_byte(data)
        # The chip acts on the command a little BEFORE the last stop bit has
        # finished going out, so by the time this returns a STEP has already
        # executed its instruction. The +16 keeps that true at low baud rates.
        await ClockCycles(self.dut.clk, self.clk_per_bit + 16)

    async def uart_write(self, addr, data):
        """WRITE one byte, over the actual wire.  1104 clocks."""
        await self.uart_cmd(CMD_WRITE, addr, data)

    async def uart_read(self, addr):
        """READ one byte, over the actual wire."""
        await self.uart_cmd(CMD_READ, addr, 0)
        return await self.recv_byte()

    async def uart_ping(self):
        """PING.  Should answer 0xAA.

        A PING that works does not mean the link works.  0xF0 already has its
        top bit set and 0xAA is a fixed pattern, so a receiver whose bit period
        is slightly wrong still gets both of them right — see Lab 5."""
        await self.uart_cmd(CMD_PING)
        return await self.recv_byte()

    async def uart_get_pc(self):
        """GET_PC, over the wire."""
        await self.uart_cmd(CMD_GET_PC)
        return await self.recv_byte()


# ── comparing against a model ────────────────────────────────────────────────

async def trace(sp, n_instr, model=None):
    """Single-step `n_instr` instructions, recording the state after each one.

    Returns `(steps, problem)`.  `steps` is a list of
    `(index, address, instruction_word, snapshot)`.  `problem` is None if all
    was well, or a string naming the FIRST disagreement with `model` — which is
    the difference between "something is wrong somewhere" and "instruction 6,
    at address 6, SUB r1, r0, put 246 in r1 where the model says 10".

    `model` is a `Golden` from golden.py, positioned at the same PC.

    Stepping is slower than free-running, because every instruction costs a
    whole UART command.  Use `run()` when you want the answer and `trace()`
    when you want to know where it went wrong."""
    steps = []
    for k in range(n_instr):
        address = sp.pc()
        word = sp.peek(address) if address < MEM_DEPTH else None
        await sp.step()
        snap = sp.snapshot()
        steps.append((k, address, word, snap))
        if model is None:
            continue
        result = model.step()
        if isinstance(result, str):
            return steps, f"the model stopped at instruction {k}: {result}"
        if model.snapshot() != snap:
            m = model.snapshot()
            return steps, (
                f"instruction {k}, at address {address} "
                f"(0x{word:02X} = {disasm(word)}), left the machine in a "
                f"different state:\n"
                f"      model: r={m[0]} PC={m[1]} N={m[2]} Z={m[3]}\n"
                f"        DUT: r={snap[0]} PC={snap[1]} N={snap[2]} Z={snap[3]}")
    return steps, None
