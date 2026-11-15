"""
DD104 — the reference test suite.

Eleven tests.  Together they catch **all thirteen** bugs in the catalogue:

    make check-all TB=test_reference

`test_example.py` is the one you copy and build on; it catches ten of the
thirteen, and the three it misses are the three that need a *different kind of
test*, not a bigger one.  This file is what "different kind" looks like:

    R08  counts a handshake instead of a value
    R09  asserts a property that must hold on EVERY cycle, not at the end
    R11  sweeps a parameter instead of using its default

Read it after you have written your own.  Reading it first turns five labs of
finding things into one lab of copying.

The other thing worth noticing is how ordinary each test is.  There is no
clever machinery here — every one of them is a short program, a run, and a
comparison.  What makes them work is entirely in the *choice of stimulus*: not
subtracting a number from itself, not shifting by one, not branching only
forwards, not ORing in bits that were already set.  Verification is mostly
taste about inputs.
"""

import random

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb

from simproc import SimProc, PARK
from simproc_asm import (ORI, ADD, SUB, NAND, SHL, SHR, LOAD, STORE,
                         JMP, BNZ, BZ, BPZ, assemble, listing, set_reg)
from golden import Golden

SAFE = 0x30         # a RAM address well clear of any program in this file


# ─────────────────────────────────────────────────────────────────────────────
# R01  ALU values, on operands chosen so a swap cannot hide
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R01_alu_asymmetric_operands(dut):
    """ADD, SUB and NAND with rA != rB and two different values.

    Catches: a swapped subtract, NAND wired as NOR, a write-back that uses the
    wrong register field."""
    sp = SimProc(dut)
    await sp.start()

    prog = set_reg(1, 200) + set_reg(2, 60) + [ADD(1, 2), SUB(1, 2), NAND(1, 2)]
    await sp.run(prog)
    assert sp.regs() == (60, 247, 60, 0), (
        f"registers are {sp.regs()}, expected (60, 247, 60, 0).\n"
        f"  200 + 60 wraps to 4; 4 - 60 wraps to 200; ~(200 & 60) = 247.\n"
        f"  {sp.describe()}")

    # And the reverse subtraction, so a swap is wrong in both directions.
    await sp.run(set_reg(1, 60) + set_reg(2, 200) + [SUB(1, 2)])
    assert sp.reg(1) == 116, f"60 - 200 should wrap to 116, got {sp.reg(1)}"


# ─────────────────────────────────────────────────────────────────────────────
# R02  ORI, with immediates that overlap what is already there
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R02_ori_overlapping_immediates(dut):
    """Three ORIs into a register that is not zero.

    The first ORI after reset is `0 | imm`, and `0 | imm == 0 + imm`, so it is
    correct even on a core whose ORI adds instead of ORs.  On a core that
    writes the answer to the wrong register it is the right value in the wrong
    place, because after reset every register holds the same thing: zero.

    You have to OR a bit that is already set before the adding core shows up,
    and you have to look at r0 itself, not just at the value, to see the other
    one.  5 | 3 is 7.  5 + 3 is 8."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run([ORI(5), ORI(3), ORI(24)])
    assert sp.reg(0) == 31, (
        f"r0 is {sp.reg(0)}, expected 31.\n"
        f"  5 | 3 = 7, then 7 | 24 = 31. If you got 32, the immediates were "
        f"ADDED, not ORed: 5 + 3 = 8, 8 + 24 = 32.\n"
        f"  {sp.describe()}")
    assert sp.regs()[1:] == (0, 0, 0), (
        f"ORI wrote something other than r0: registers are {sp.regs()}.\n"
        f"  ORI has no register field — all five spare bits are the immediate — "
        f"so r0 is the only register it can touch.")


# ─────────────────────────────────────────────────────────────────────────────
# R03  every shift amount the field can hold, both directions
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R03_shift_amount_sweep(dut):
    """Shift by 0, 1, 2 and 3 — not just by 1.

    The amount field is two bits wide.  A test that only ever shifts by one has
    tested one of its four values, and 'shift by 1' is what everybody writes."""
    sp = SimProc(dut)
    await sp.start()

    for amount in range(4):
        await sp.run(set_reg(1, 0b0011_0110) + [SHL(1, amount)])
        want = (0b0011_0110 << amount) & 0xFF
        assert sp.reg(1) == want, (
            f"0x36 << {amount} gave 0x{sp.reg(1):02X}, expected 0x{want:02X}")

    for amount in range(4):
        await sp.run(set_reg(1, 0b1011_0110) + [SHR(1, amount)])
        want = (0b1011_0110 >> amount) & 0xFF
        assert sp.reg(1) == want, (
            f"0xB6 >> {amount} gave 0x{sp.reg(1):02X}, expected 0x{want:02X}. "
            f"SimProc's right shift is logical — zeros come in at the top.")


# ─────────────────────────────────────────────────────────────────────────────
# R04  every branch displacement, forwards AND backwards
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R04_branch_displacement_sweep(dut):
    """All sixteen displacements a 4-bit signed field can hold.

    Forwards is the half you test first, because 'skip the next instruction' is
    the first branch anyone writes.  It is also the half that stays correct if
    the displacement is zero-extended instead of sign-extended — the negative
    half lands 16 instructions too far forward, and the first loop you write
    never terminates."""
    sp = SimProc(dut)
    await sp.start()
    wrong = []
    for disp in range(-8, 8):
        sp.poke(20, JMP(disp))
        await sp.set_pc(20)
        await sp.step()
        want = 21 + disp
        got = sp.pc()
        if got != want:
            wrong.append((disp, want, got))
    assert not wrong, (
        "branch displacements landed in the wrong place:\n" +
        "\n".join(f"    JMP {d:+d} from address 20 -> PC {g}, expected {w}"
                  for d, w, g in wrong) +
        "\n  target = (address of the branch) + 1 + displacement.")


# ─────────────────────────────────────────────────────────────────────────────
# R05  one compare, two branches
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R05_flags_survive_a_branch(dut):
    """Compare once, branch on the result twice.

    Branches do not set flags, so this is legal and it is an idiom you write on
    day one — `BZ somewhere; BNZ somewhere_else`.  It is also the only way to
    notice a branch that quietly writes the flags with its own PC arithmetic:
    with one branch per compare, everything works."""
    sp = SimProc(dut)
    await sp.start()

    prog = assemble("""
            SUB   r1, r1        # r1 = 0  ->  Z = 1, N = 0
            BZ    taken         # taken
            ORI   16            # skipped
    taken:  BNZ   wrong         # must NOT be taken: Z is still 1
            ORI   1             # r0 = 1, the proof we got here
            JMP   done
    wrong:  ORI   8             # r0 = 8 if the flags were clobbered
    done:   SUB   r3, r3
    """)
    dut._log.info("\n" + listing(prog))
    await sp.run(prog)
    assert sp.reg(0) == 1, (
        f"r0 is {sp.reg(0)}, expected 1.\n"
        f"  8 means the second branch was taken, so Z changed between the "
        f"compare and it — but the only thing in between was a branch, and "
        f"branches are not supposed to touch the flags.\n"
        f"  {sp.describe()}")


# ─────────────────────────────────────────────────────────────────────────────
# R06  LOAD and STORE with every operand distinct
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R06_load_store_distinct_registers(dut):
    """The data register, the pointer register and the destination are three
    different registers, and the two pointers are different addresses.

    This one is here because of a mistake I made writing it.  My first version
    used `LOAD r1, r1` — load through a pointer into itself, which is a real
    idiom and reads perfectly naturally.  It also passes on a core that takes
    the address from the WRONG register, because when the two registers are the
    same register there is no wrong one.  I only found out by injecting the bug
    and watching my own test pass.

    Make every operand distinct on purpose.  Aliasing hides bugs, and the
    aliases you write by habit are the ones you will never suspect."""
    sp = SimProc(dut)
    await sp.start()

    prog = (set_reg(1, SAFE) +          # r1 = 0x30, the first pointer
            set_reg(2, 0x5A) +          # r2 = 0x5A, the data
            set_reg(3, SAFE + 5) +      # r3 = 0x35, the second pointer
            [STORE(2, 1),               # mem[0x30] = 0x5A
             LOAD(0, 1),                # r0 = mem[0x30]      (via r1, into r0)
             STORE(0, 3)])              # mem[0x35] = 0x5A    (via r3)
    await sp.run(prog)

    assert sp.peek(SAFE) == 0x5A, f"mem[0x30] is 0x{sp.peek(SAFE):02X}, expected 0x5A"
    assert sp.reg(0) == 0x5A, (
        f"r0 is 0x{sp.reg(0):02X}, expected 0x5A.\n"
        f"  LOAD r0, r1 reads mem[r1]. r1 holds 0x{SAFE:02X}; r0 held "
        f"0x{sp.peek(SAFE):02X} before the load.\n  {sp.describe()}")
    assert sp.peek(SAFE + 5) == 0x5A, (
        f"mem[0x35] is 0x{sp.peek(SAFE + 5):02X}, expected 0x5A")


# ─────────────────────────────────────────────────────────────────────────────
# R07  the flags themselves, on values chosen to break a lazy detector
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R07_zero_and_negative_flags(dut):
    """Z and N, on bytes whose bottom nibble is zero and whose top is not.

    16, 32, 64 and 128 are all non-zero and all end in four zero bits.  A
    zero-detector wired to only part of the byte says Z = 1 for every one of
    them, and no amount of checking register VALUES will ever notice — the
    values are all correct."""
    sp = SimProc(dut)
    await sp.start()

    for value in (16, 32, 64, 128):
        await sp.run(set_reg(1, value) + [ADD(1, 3)])   # r3 is 0: r1 keeps `value`
        n, z = sp.flags()
        assert sp.reg(1) == value, f"r1 is {sp.reg(1)}, expected {value}"
        assert z == 0, (
            f"after r1 = {value} (0b{value:08b}) the Z flag is 1.\n"
            f"  {value} is not zero. Its bottom four bits are, which is the "
            f"whole point of picking it.")
        assert n == (1 if value >= 128 else 0), (
            f"after r1 = {value} the N flag is {n}; N is bit 7 of the result")

    await sp.run([SUB(1, 1)])
    assert sp.flags() == (0, 1), f"after r1 = 0 the flags are {sp.flags()}, expected (0, 1)"

    # And the consequence, which is what actually bites: a branch on a bad flag.
    # SUB(0, 0) clears r0 BEFORE the compare, because ORI only sets bits and r0
    # is still holding 16 from the last set_reg. Clearing it after the compare
    # would set the flags again and destroy the thing being tested.
    prog = set_reg(1, 16) + [SUB(0, 0), ADD(1, 3), BZ(1), ORI(1), SUB(3, 3)]
    await sp.run(prog)
    assert sp.reg(0) == 1, (
        f"r0 is {sp.reg(0)}, expected 1: the BZ after r1 = 16 was TAKEN, so the "
        f"core thinks 16 is zero.")


# ─────────────────────────────────────────────────────────────────────────────
# R08  the handshake, counted
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R08_done_pulses_once_per_instruction(dut):
    """`done` must pulse exactly once for every instruction that retires.

    Nothing in this test looks at a register, a memory location or a flag.  All
    of those can be perfectly correct on a core that forgets to raise `done` for
    one instruction — and if your scoreboard samples on `done`, that core does
    not make your tests fail.  It makes them stop scoring, silently, from that
    instruction onwards.  A test that passes because it checked nothing is the
    thing this whole course is about."""
    sp = SimProc(dut)
    await sp.start()

    prog = (set_reg(2, SAFE) +
            [ORI(1), ADD(1, 0), STORE(1, 2), SUB(1, 0), STORE(1, 2),
             NAND(1, 1), SHL(1, 1), ADD(1, 2), STORE(1, 2)])
    cycles, reason = Golden(prog).run(len(prog))
    assert reason is None, reason

    await sp.load(prog)
    await sp.set_pc(0)
    pulses = await sp.count_done_pulses(cycles)
    assert pulses == len(prog), (
        f"{len(prog)} instructions retired in {cycles} clock cycles, but `done` "
        f"pulsed {pulses} times.\n"
        f"  There are {sum(1 for w in prog if (w & 0xF) == 0b0010)} STOREs in "
        f"this program, and {len(prog) - pulses} pulses are missing.")


# ─────────────────────────────────────────────────────────────────────────────
# R09  a property that must hold on every single cycle
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R09_halt_stays_low_while_running(dut):
    """While RUN is asserted, `halt` must be low on every cycle.

    A core that drops into IDLE for one cycle after an instruction and then
    restarts computes exactly the same answers.  Every register, every byte of
    memory, every flag: identical.  It just takes one cycle longer, and a
    debugger watching the halt pin sees a glitch that is not supposed to exist.

    Functional equivalence is not correctness, and the only thing that can tell
    the difference is an assertion about a signal over time."""
    sp = SimProc(dut)
    await sp.start()

    prog = (set_reg(2, SAFE) +
            [ORI(3), ADD(1, 0), STORE(1, 2), SUB(1, 0), STORE(1, 2),
             ADD(1, 0), STORE(1, 2)])
    cycles, reason = Golden(prog).run(len(prog))
    assert reason is None, reason

    await sp.load(prog)
    await sp.set_pc(0)
    halts = await sp.count_halt_cycles(cycles)
    assert halts == 0, (
        f"`halt` was high on {halts} of the first {cycles} cycles of a program "
        f"that never stopped running.\n"
        f"  halt means 'the core is in IDLE'. Between two instructions of a "
        f"free-running program there is no IDLE state — the core goes straight "
        f"from retiring one instruction to fetching the next.")


# ─────────────────────────────────────────────────────────────────────────────
# R10  random programs against the model
# ─────────────────────────────────────────────────────────────────────────────

def random_program(seed, n=20):
    """Arithmetic, shifts, ORI, and forward branches that cannot loop.

    No LOAD or STORE: a random register value is a random address, and half of
    them are outside the 64-byte RAM. No backward branches: a random loop is an
    infinite loop. Both of those are worth testing — with stimulus you designed
    rather than stimulus you rolled."""
    rnd = random.Random(seed)
    prog = []
    for i in range(n):
        late = i >= n - 4          # keep the tail branch-free so nothing can
        kind = rnd.choice(["alu", "alu", "shift", "ori"] +
                          ([] if late else ["branch"]))   # jump past the park
        if kind == "alu":
            prog.append(rnd.choice([ADD, SUB, NAND])(rnd.randint(0, 3), rnd.randint(0, 3)))
        elif kind == "shift":
            prog.append(rnd.choice([SHL, SHR])(rnd.randint(0, 3), rnd.randint(0, 3)))
        elif kind == "ori":
            prog.append(ORI(rnd.randint(0, 31)))
        else:
            prog.append(rnd.choice([JMP, BNZ, BZ, BPZ])(rnd.randint(0, 3)))
    return prog


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R10_random_programs(dut):
    """Eight random programs, each compared against golden.py at the end.

    Random stimulus is cheap and it finds things nobody thought of.  It is also
    the weakest test in this file, and worth being honest about why: with no
    coverage model behind it, it only samples.  Every one of these programs
    could run and still never once produce a non-zero byte whose bottom nibble
    is zero — so a broken Z flag would survive all eight.  R07 exists because
    random testing does not replace thinking about the input."""
    sp = SimProc(dut)
    await sp.start()

    bad = []
    for seed in range(8):
        prog = random_program(seed)
        # Reset between programs. The RAM survives a reset and the registers do
        # not, which is exactly what is wanted: the model starts from zero, so
        # the chip has to as well. Leave this out and program 2 starts with
        # program 1's registers still in it, and every comparison after the
        # first one is meaningless.
        await sp.reset()
        await sp.run(prog)
        model = Golden(prog + [PARK])
        cycles, reason = model.run(200)
        if model.snapshot()[0] != sp.regs():
            bad.append((seed, model.snapshot()[0], sp.regs(), prog))
    assert not bad, (
        f"{len(bad)} of 8 random programs disagreed with the model.\n" +
        "\n".join(f"  seed {s}: model r={m}, chip r={d}\n{listing(p)}"
                  for s, m, d, p in bad[:1]))
    dut._log.info("8 random programs, 8 agreements")


# ─────────────────────────────────────────────────────────────────────────────
# R11  sweep the parameter
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def R11_baud_sweep(dut):
    """The UART, at five different bit periods, with a real byte in each.

    `clk_per_bit` is uio_in x 4, and a test suite that only ever uses the
    default has tested one point of a range that silicon will be used across.

    Note what is checked at each speed.  PING is not enough: 0xF0 already has
    its top bit set, and the reply 0xAA is a fixed pattern, so a receiver whose
    bit period is one clock too long still gets both of them right while
    mangling every byte that carries data.  A link test that can pass over a
    broken link is not a link test."""
    sp = SimProc(dut)
    await sp.start()

    failures = []
    for uio in (4, 8, 16, 32, 64):
        await sp.set_baud(uio)
        try:
            reply = await sp.uart_ping()
        except Exception as e:                      # noqa: BLE001
            failures.append((uio, sp.clk_per_bit, f"PING: {type(e).__name__}"))
            continue
        if reply != 0xAA:
            failures.append((uio, sp.clk_per_bit, f"PING answered 0x{reply:02X}"))
            continue
        # Now a byte that is not a fixed pattern, through memory and back.
        try:
            await sp.uart_write(SAFE, 0x5A)
            got = await sp.uart_read(SAFE)
        except Exception as e:                      # noqa: BLE001
            failures.append((uio, sp.clk_per_bit,
                             f"PING was fine, then WRITE/READ raised "
                             f"{type(e).__name__}: {str(e).splitlines()[0][:70]}"))
            continue
        if got != 0x5A:
            failures.append((uio, sp.clk_per_bit,
                             f"PING was fine, then wrote 0x5A and READ gave "
                             f"back 0x{got:02X}"))
        else:
            dut._log.info(f"uio_in={uio:3d}  clk_per_bit={sp.clk_per_bit:4d}  "
                          f"PING 0xAA, 0x5A round-tripped")

    assert not failures, (
        "the UART did not work at every speed it is specified for:\n" +
        "\n".join(f"    uio_in={u:3d}  clk_per_bit={c:4d}   {why}"
                  for u, c, why in failures) +
        "\n  Note which speeds are fine. A receiver whose bit period is one "
        "clock\n  too long walks further off centre with every bit, so it "
        "fails at short\n  bit periods first and is invisible at long ones.")
