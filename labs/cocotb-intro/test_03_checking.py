"""
DD104 — driving and checking a design.

This is the testbench the lab's verdict is built on.  It has to do two things,
and the second one is the one people forget:

    make sim       PASS against rtl/counter.sv
    make broken    FAIL against rtl/counter_broken.sv

A testbench that only ever passes has told you nothing.  Every assertion in
here is written so that its FAILURE message alone is enough to start fixing
the design -- no re-running, no adding prints, no opening a waveform.
"""

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from cocotb.utils import get_sim_time


async def start(dut, period_ns=10):
    """Clock, reset, and a design in a known state.  Every test starts here."""
    cocotb.start_soon(Clock(dut.clk, period_ns, unit="ns").start())
    dut.rst_n.value = 0
    dut.en.value    = 0
    dut.load.value  = 0
    dut.d.value     = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await Timer(1, unit="ns")


async def tick(dut, n=1):
    """Advance n clock edges and come back 1 ns later, when q has settled.

    Wrapping this up is worth doing once.  Every `await RisingEdge(clk)` in a
    test body is a place where somebody will eventually forget the settle
    time and read a stale value -- and stale values do not raise, they just
    make a passing test wrong.
    """
    await ClockCycles(dut.clk, n)
    await Timer(1, unit="ns")


def state(dut):
    """One line describing the whole design. Paste it into failure messages."""
    return (f"q=0x{int(dut.q.value):02X} tc={dut.tc.value} "
            f"en={dut.en.value} load={dut.load.value} "
            f"rst_n={dut.rst_n.value} at t={get_sim_time('ns'):.0f} ns")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Load, then count: the ordinary path
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def load_then_count(dut):
    """load puts a value in; en advances it by exactly one per clock."""
    await start(dut)

    dut.load.value = 1
    dut.d.value    = 0x30
    await tick(dut)
    dut.load.value = 0
    assert dut.q.value == 0x30, (
        f"load of 0x30 did not take: q is 0x{int(dut.q.value):02X}\n  {state(dut)}")

    dut.en.value = 1
    for expected in range(0x31, 0x31 + 8):
        await tick(dut)
        got = int(dut.q.value)
        assert got == expected, (
            f"counting from 0x30: expected 0x{expected:02X}, got 0x{got:02X} "
            f"-- a difference of {got - expected:+d}\n  {state(dut)}")

    dut._log.info(f"counted 0x30 -> 0x{int(dut.q.value):02X}, one per clock")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  en low means en low
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def enable_holds_the_count(dut):
    """With en low, twenty clocks change nothing.

    Test the case where the design is supposed to do NOTHING.  It is the half
    of the specification nobody writes a test for, and 'does nothing' is a
    result exactly as much as 'adds one' is.
    """
    await start(dut)
    dut.load.value = 1
    dut.d.value    = 0x7E
    await tick(dut)
    dut.load.value = 0
    dut.en.value   = 0

    await tick(dut, 20)
    got = int(dut.q.value)
    assert got == 0x7E, (
        f"with en low for 20 clocks the count moved from 0x7E to 0x{got:02X} "
        f"({got - 0x7E:+d})\n  {state(dut)}")
    dut._log.info("20 clocks with en low: q unchanged at 0x7E")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  load beats en — the priority the RTL commits to
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def load_wins_over_enable(dut):
    """Both controls high at once. Somebody has to win; check it is load.

    Priority between two controls is real, checkable behaviour that lives in
    the ORDER of two `else if` branches -- exactly the kind of thing an editor
    reorders while tidying up, with no warning from any tool.
    """
    await start(dut)
    dut.load.value = 1
    dut.d.value    = 0x11
    dut.en.value   = 1
    await tick(dut)
    got = int(dut.q.value)
    assert got == 0x11, (
        f"with load AND en both high, q became 0x{got:02X}.\n"
        f"  0x11 means load won (correct for this design).\n"
        f"  0x12 means load won and en also applied.\n"
        f"  anything else means en won.\n  {state(dut)}")
    dut._log.info("load and en both high: load wins, q = 0x11")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  tc — the output a value-only test never looks at
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def terminal_count_needs_enable(dut):
    """tc is `en & (q == 255)`, and the `en &` is the half that gets lost.

    Every other test in this file would pass on a counter whose tc is just
    `q == 255`, because they never look at tc, or look at it only while
    counting -- which is exactly when both versions agree.

    Park the counter at 255 with en LOW.  A correct tc is 0 there: the count
    is not about to wrap, because the count is not moving.  This is the
    assertion that `make broken` fails.
    """
    await start(dut)

    dut.load.value = 1
    dut.d.value    = 0xFF
    await tick(dut)
    dut.load.value = 0
    dut.en.value   = 0
    await tick(dut)

    assert int(dut.q.value) == 0xFF, f"could not park the counter at 0xFF\n  {state(dut)}"

    tc = dut.tc.value
    assert tc == 0, (
        f"q is 0xFF and en is 0, so the count is NOT about to wrap, but tc is {tc}.\n"
        f"  tc should be `en & (q == 8'hFF)`. A tc of 1 here means the `en &`\n"
        f"  is missing and tc is really just `q == 8'hFF`.\n"
        f"  Everything about the COUNT is still correct -- only the flag is wrong,\n"
        f"  and only while en is low.\n  {state(dut)}")

    # ...and now prove tc can be 1 at all, so a tc stuck at 0 cannot pass.
    dut.en.value = 1
    await Timer(1, unit="ns")
    assert dut.tc.value == 1, (
        f"q is 0xFF and en is 1, so tc should be 1, but it is {dut.tc.value}.\n"
        f"  {state(dut)}")
    dut._log.info("tc: 0 at q=0xFF with en low, 1 at q=0xFF with en high")


# ─────────────────────────────────────────────────────────────────────────────
# 5.  The wrap, and the cycle it happens on
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def the_wrap_is_where_the_bugs_live(dut):
    """255 -> 0, checked on the exact cycle, with tc checked on both sides."""
    await start(dut)
    dut.load.value = 1
    dut.d.value    = 0xFD
    await tick(dut)
    dut.load.value = 0
    dut.en.value   = 1

    seen = []
    for _ in range(5):
        await tick(dut)
        seen.append((int(dut.q.value), int(dut.tc.value)))

    dut._log.info("q, tc across the wrap: " +
                  " ".join(f"({q:3d},{t})" for q, t in seen))

    expected = [(0xFE, 0), (0xFF, 1), (0x00, 0), (0x01, 0), (0x02, 0)]
    assert seen == expected, (
        f"across the wrap this counter produced\n"
        f"    {seen}\n"
        f"  and the specification says\n"
        f"    {expected}\n"
        f"  (q, tc) pairs, one per clock, starting from q=0xFD.\n"
        f"  tc is high on the cycle where q IS 255 -- the cycle before it wraps,\n"
        f"  not the cycle after.\n  {state(dut)}")


# ─────────────────────────────────────────────────────────────────────────────
# 6.  A reference model, and 400 random clocks against it
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def against_a_reference_model(dut):
    """Six lines of Python that are the counter, checked every single clock.

    Directed tests check the cases you thought of.  This one checks the cases
    you did not -- and when it fails it reports the FIRST clock where the two
    disagreed, which is the only cycle number worth having.

    The seed is pinned so that this test means the same thing on your machine
    as it does in the guide.  That matters more than it sounds: a random test
    with a floating seed passes on Tuesday and fails on Wednesday, and you
    cannot tell whether you changed the design or drew a different hand.

    Read the honest limitation too, because it is the more useful half of
    this test.  The tc bug in rtl/counter_broken.sv is only visible when the
    counter sits at 0xFF with en LOW.  With this seed, that happens on
    exactly 0 of these 600 clocks -- the count reaches 0xFF only while it is
    running, and while it is running the broken tc and the correct tc agree.
    So this test, 600 clocks of it, PASSES on the broken counter.  It is the
    forty-line directed test above that catches it, every time, on purpose.

    Random stimulus finds bugs it was not aimed at by accident.  Do not
    mistake volume for coverage.
    """
    await start(dut)
    rng = random.Random(104)
    model_q = 0
    at_ff_with_en_low = 0

    for cycle in range(600):
        en   = rng.random() < 0.7
        load = rng.random() < 0.1
        d    = rng.randrange(256)

        dut.en.value   = int(en)
        dut.load.value = int(load)
        dut.d.value    = d

        # The model, applied with the same priority the RTL uses.
        if load:      model_q = d
        elif en:      model_q = (model_q + 1) & 0xFF
        model_tc = 1 if (en and model_q == 0xFF) else 0
        if model_q == 0xFF and not en:
            at_ff_with_en_low += 1

        await tick(dut)

        got_q = int(dut.q.value)
        assert got_q == model_q, (
            f"clock {cycle}: q is 0x{got_q:02X}, model says 0x{model_q:02X}\n"
            f"  inputs this cycle: en={int(en)} load={int(load)} d=0x{d:02X}\n"
            f"  {state(dut)}")

        got_tc = int(dut.tc.value)
        assert got_tc == model_tc, (
            f"clock {cycle}: tc is {got_tc}, model says {model_tc}\n"
            f"  q=0x{got_q:02X} en={int(en)} -- tc must be `en & (q == 0xFF)`\n"
            f"  {state(dut)}")

    dut._log.info(f"600 random clocks, q and tc agreed with the model on every one "
                  f"(final q = 0x{model_q:02X})")
    dut._log.info(f"of those 600 clocks, {at_ff_with_en_low} had q = 0xFF with en low "
                  f"-- the only ones where a broken tc would have shown")
