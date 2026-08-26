# The handshake is part of the contract

**Question this page answers:** *Every register, every flag and every byte of memory is correct. How can it still be broken?*

Because being right is not the whole job. Being right **at the agreed moment** is the other
half, and nothing in a register dump can see it.

Two of the thirteen bugs in this course are like that. Here is one of them running against the
most thorough value-checking testbench in the repository:

```bash
cd labs/common
make check TB=test_values_only BUG=B08
```

```
      ok  the golden core                    3 tests, all passed             20.0s
  MISSED  B08_store_drops_done               3 tests, all passed             19.2s
------------------------------------------------------------------------
 VERDICT: FAIL — your testbench passes B08_store_drops_done too.
   That bug hides behind: checking values instead of the handshake
```

`B08_store_drops_done` changes one line so that `STORE` no longer pulses the `done` output. The
byte still lands in memory. The address is right, the data is right, the program counter is
right, the flags are right, the cycle count is right. **One pin does not twitch.**

Run the shipped six-test example against it and you get the same `MISSED`. Run the eleven-test
reference suite and exactly one test fires:

```bash
make check TB=test_reference BUG=B08
```

```
  caught  B08_store_drops_done               11 tests, 1 FAILED              18.2s
        R08_done_pulses_once_per_instruction
            AssertionError: 15 instructions retired in 60 clock cycles, but `done` pulsed 12 times.
```

**Fifteen and twelve.** Three of the fifteen instructions were `STORE`. Ten of the eleven
reference tests pass on this core, including the one that steps a program and compares every
register, the PC and both flags against a Python model after every single instruction — because
the model has no idea `done` exists.

> Here is where an intuition from software betrays you. In software, "returned the right value"
> is usually the whole contract; *when* it returned is a performance question. In hardware,
> *when* is part of the specification, it has a name — the handshake — and a downstream block
> that was watching for a pulse and did not see one does not get a late answer. It gets no
> answer.

And the reason it matters more than it looks: `done` is what a scoreboard triggers on. A missing
pulse does not make such a test *fail*. It makes it quietly stop scoring, and it goes on
reporting green about a stretch of the program it is no longer looking at.

## The other one: right answer, one cycle late

`B13_store_falls_to_idle` is the same family and even smaller. `STORE` drops back through the
core's idle state on its way to the next instruction, instead of going straight there. Every
result is identical. Every byte of memory is identical. It costs **one clock cycle**, once per
`STORE`.

```bash
make check TB=test_example BUG=B13
```

```
  caught  B13_store_falls_to_idle            6 tests, 1 FAILED                5.8s
        t05_a_loop_and_its_cycle_count
            AssertionError: the program took 110 clock cycles, expected 109.
```

**110 against 109.** That is the entire symptom. The test that catches it is the one that
asserted a cycle count it had worked out by hand:

```
    setup    4+5+4+4+4+5+4                = 30
    loop     (ADD 4 + SUB 4 + BNZ 3) x 5  = 55
    finish   4+5+4+4+4+3                  = 24
                                            ---
                                            109
```

**Why an engineer cares:** an assertion on a number you derived from the datasheet costs one
line and catches a whole class of bug that no value comparison can reach. If the answer had come
back 114 instead of 110, the difference of five would have told you it was once per loop
iteration. *A cycle count is a property, and properties are cheap to assert.*

## Now the wire, where the same idea has teeth

SimProc talks over a UART. The harness in
[`simproc.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/simproc.py) contains a
**bus functional model** — a *BFM*, meaning Python that pretends to be the device on the other
end of a wire and knows the protocol and nothing else about the design. Its `send_byte()` sends
a start bit, eight data bits, a stop bit… and then one more bit period of idle line, with a
comment saying that gap is required.

That comment is the subject of the rest of this page, and it ships as a measurement:
[`labs/common/test_handshake_timing.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_handshake_timing.py).

```bash
make sim TB=test_handshake_timing
```

Four tests, 90,910 ns of simulated time, under a second of wall clock.

## Where the receiver actually spends its time

`t01` puts a state monitor on `UART_RX1.state` and sends one byte at the default speed
(`uio_in = 8`, so `clk_per_bit = 32`):

```python
async def watch_rx(sp, cycles):
    """Record (state_name, how_many_clocks) for the receiver, for `cycles`."""
    rx = sp.sys.UART1.UART_RX1
    runs = []
    for _ in range(cycles):
        await RisingEdge(sp.dut.clk)
        name = RX_STATES[int(rx.state.value)]
        if runs and runs[-1][0] == name:
            runs[-1][1] += 1
        else:
            runs.append([name, 1])
    return [(n, c) for n, c in runs]
```

**What you should see:**

```
clk_per_bit = 32; receiver states: START=16  RECEIVE=288  DONE=32
the frame on the wire is 320 clocks; the receiver is busy for 336 -- 16 clocks LONGER,
which is 0.50 of a bit period
```

Three numbers, and each one comes straight out of the RTL:

| state | clocks | why |
|---|---|---|
| `START` | **16** | it leaves when `clkCount == (clk_per_bit-1)>>1` = 15, counting from 0, so it occupies 16 — half a bit period, to land in the *middle* of the start bit |
| `RECEIVE` | **288** | 9 × 32: eight data bits **and the parity bit** |
| `DONE` | **32** | one whole further bit period, holding the byte, before it will look at the line again |

Add them: 16 + 288 + 32 = **336**. The frame you put on the wire was 10 bit periods —
start, eight data, stop — which is **320**. The receiver is busy for **exactly half a bit period
longer than the frame it just received**, every time.

That is the fact to carry away. The chip is not ready when your frame ends. It is ready
16 clocks later, and 16 is `clk_per_bit / 2`.

The test asserts the formula, not just the number, so it stays true at other baud rates. Swept
across four settings, it does:

| `uio_in` | `clk_per_bit` | START | RECEIVE | DONE | busy | frame | excess |
|---|---|---|---|---|---|---|---|
| 4 | 16 | 8 | 144 | 16 | 168 | 160 | 8 |
| 8 | 32 | 16 | 288 | 32 | 336 | 320 | 16 |
| 12 | 48 | 24 | 432 | 48 | 504 | 480 | 24 |
| 16 | 64 | 32 | 576 | 64 | 672 | 640 | 32 |

The excess is `clk_per_bit / 2` in all four rows.

## A BFM that ignores it corrupts the next byte

`t02` sends the same three bytes twice. Once through the harness's `send_byte()`, which leaves
the gap. Once through `send_frame_only()`, which is `send_byte()` with its last two lines
deleted — the version almost everybody writes first:

```python
async def send_frame_only(sp, value):
    """One 8N1 frame and NOTHING else -- no trailing idle."""
    frame = [0] + [(value >> i) & 1 for i in range(8)] + [1]
    for b in frame:
        sp.dut.ui_in.value = b
        await ClockCycles(sp.dut.clk, sp.clk_per_bit)
```

The command is `SET_PC 12`: three bytes, `0x99 0x0C 0x00`.

**What you should see:**

```
sent    : 0x99 0x0C 0x00
received: 0x99 0x86 0x80
with the inter-frame gap: PC = 12.  Without it: PC = 134.
```

Nothing errored. Nothing warned. Every bit was on the wire for exactly one bit period. And the
program counter is 134.

Follow the bytes, because the corruption has a shape and the shape is the diagnosis:

- **`0x99` arrived intact.** The receiver was idle before it, so it caught the start bit on
  time.
- **`0x0C` arrived as `0x86`.** `0x0C` is `0000 1100`. `0x86` is `1000 0110`. That is `0x0C`
  shifted **right** by one, with a `1` in the new top bit: `(0x0C >> 1) | 0x80 = 0x86`. Every
  bit was sampled one bit period **late**, so bit *i* of the received byte is bit *i+1* of the
  sent one, and the top bit came from the stop bit — which is always 1.
- **`0x00` arrived as `0x80`.** `(0x00 >> 1) | 0x80`. Same rule. For *these* three bytes the
  test pins the result to the digit — `assert got == late and bad == late[1]` — because a
  prediction you can check is worth more than a shrug.
- **`134` is `0x86`.** The corrupted address byte, straight into the program counter.

The receiver was still in `DONE` when your second start bit began, missed the falling edge,
picked up the *next* falling edge instead, and never recovered — every subsequent frame is late
by the same amount.

## And the reason nobody catches it

`t03` sends `PING` the same broken way:

```
gapless PING answered 0xAA -- a green light on a link that just corrupted two of its three bytes
```

`PING` is `0xF0`, and it **ignores its address and data bytes**. So the two frames that get
mangled are the two nobody reads, and the reply is a fixed `0xAA` either way. Your link test
passes. Every command that carries an argument is broken.

> **A link test that passes over a broken link is worse than no link test.** It is the same
> shape as the shipped test that asserts the processor is not running: a green light that was
> never wired to the thing it claims to be about.

## Two more numbers your testbench already depends on

`t04` measures the two constants the harness is built on, and checks each against arithmetic
you can do on paper:

```
one 3-byte command costs 1104 clock cycles = 3 x 11 x 32 (frame + gap) + 32 + 16 = 1104
the core fetched its first instruction 57 clock cycles BEFORE uart_cmd(RUN) returned
```

**1,104** is three frames of eleven bit periods each — ten on the wire plus the mandatory gap —
plus the 48 clocks the harness waits at the end of a command. Three by eleven by thirty-two is
1,056; plus 48 is 1,104. That is why there is no way to stop this processor after exactly *N*
instructions: `HALT` takes 1,104 cycles to arrive and the core runs the whole time. It is also
why `run()` appends a parking loop instead.

**57** is the head start. The chip acts on `RUN` before the last stop bit has finished going
out, so a monitor you start *after* `start_running()` returns has already missed about fourteen
instructions. Every counting call in the harness — `run()`, `run_cycles()`,
`count_done_pulses()`, `count_halt_cycles()` — starts its watcher first for exactly this reason.
If you write your own, do the same, and the harness's `_go()` is the four lines to copy.

## Try this

Change the data and watch the corruption change shape. `COMMAND` is one line at the top of the
file, and nothing in `t02` is written as a constant:

```bash
cd labs/common
sed 's/^COMMAND = (CMD_SET_PC, 12, 0)/COMMAND = (CMD_SET_PC, 0x34, 0x12)/' \
    test_handshake_timing.py > test_gap_mine.py
make sim TB=test_gap_mine
```

**What you should see:**

```
sent    : 0x99 0x34 0x12
received: 0x99 0x9A 0x89
with the inter-frame gap: PC = 52.  Without it: PC = 154.
if every frame after the first were sampled ONE BIT PERIOD LATE, they would arrive as: 0x99 0x9A 0x89
```

The prediction and the measurement agree. Now do it twice more, with `0x0F, 0x33` and with
`0x55, 0xFF`:

| address, data | received | the "one period late" prediction | PC |
|---|---|---|---|
| `0x0C, 0x00` (shipped) | `0x99 0x86 0x80` | `0x99 0x86 0x80` ✓ | 134 |
| `0x34, 0x12` | `0x99 0x9A 0x89` | `0x99 0x9A 0x89` ✓ | 154 |
| `0x0F, 0x33` | `0x99 0x87 0xE6` | `0x99 0x87 0x99` ✗ | 135 |
| `0x55, 0xFF` | `0x99 0xAA` — **two bytes** | `0x99 0xAA 0xFF` ✗ | 0 |

All four runs still pass, because `t02` asserts only the three things that are true for *any*
three bytes: the first frame arrives intact, something later is corrupted, and the command did
not do what you asked.

**Read the last two rows.** The clean one-bit-period slip is the common case, not a law.

`0x0F, 0x33` slips cleanly on the second frame and then lands somewhere else entirely on the
third — the receiver resynchronised onto a different edge, and `0xE6` is neither the byte you
sent nor the byte a uniform one-period slip would produce.

`0x55, 0xFF` is worse and more instructive: **only two bytes ever arrive.** After its start bit,
`0xFF` is a solid run of ones — there is no falling edge anywhere in that frame for a
resynchronising receiver to latch onto. The third byte of the command simply never happens, the
chip is left waiting for it, and the program counter stays 0. A lost frame and a corrupted frame
look completely different in a log and are the same defect.

**The reflex:** *when a protocol has a recovery or turnaround period, find its length in the
RTL, make your BFM wait it out, and write a test that measures it — so you find out when
somebody changes it.* And when you pick test data, avoid the bytes that are fixed points of the
corruption you are hunting. `0x00`, `0xFF` and `0xAA` survive more transformations than any
other bytes, and they are the three everybody reaches for first.

Next: [Writing the bug report](guide/writing-the-bug-report.md). Or go to
[Lab 05](labs/lab-05-every-answer-is-right-overview.md), which is two processors on which every
answer is right.
