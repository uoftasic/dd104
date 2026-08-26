# The SimProc harness

**Question this page answers:** *What can I ask the harness for, and what does it already do for me?*

Everything on this page lives in
[`labs/common/`](https://github.com/uoftasic/dd104/tree/main/labs/common) and is importable from
any lab, because `sim.mk` puts both your lab directory and `common/` on `PYTHONPATH`.

Every worked example below is a real line out of
[`test_api_tour.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_api_tour.py),
and every output block is what it printed. Run the whole tour yourself — nine tests, 535,650 ns
of simulated time, about five seconds:

```bash
cd labs/common
make sim TB=test_api_tour
```

If a signature on this page ever stops matching the code, that file stops running.

---

## The five files

| file | what it is |
|---|---|
| `simproc.py` | **the harness.** `SimProc`, `trace()`, `bit()`, and the command constants. |
| `simproc_asm.py` | **the assembler.** Instruction helpers, `set_reg`, `assemble`, `disasm`, `listing`. Imports nothing; runs at a plain Python prompt. |
| `golden.py` | **the reference model.** The instruction set in about 120 lines of Python. Imports nothing. |
| `bugs.py` · `inject.py` · `check.py` | the catalogue, the injector and the verdict. You call these through `make`, not by hand. |
| `test_example.py` · `test_reference.py` · `test_api_tour.py` | worked testbenches. Copy the first, read the second afterwards, use the third as this page's source. |

## The shortest complete test

```python
import cocotb
from simproc import SimProc
from simproc_asm import ORI, ADD

@cocotb.test()
async def r1_gets_five(dut):
    sp = SimProc(dut)
    await sp.start()                              # clock, reset, blank memory
    cycles = await sp.run([ORI(5), ADD(1, 0)])    # r0 = 5 ; r1 = r1 + r0
    assert sp.reg(1) == 5, f"r1 is {sp.reg(1)}, expected 5"
    assert cycles == 9, f"took {cycles} cycles, expected 5 + 4"
```

```bash
cp test_example.py test_mine.py
make sim   TB=test_mine
make check TB=test_mine BUG=B01
```

`TB` names a **Python module**, not a file: `TB=test_mine`, never `TB=test_mine.py`.

---

## Setup

### `SimProc(dut, clock_ns=10, uio=8)`

Wraps the top-level handle cocotb gives you. Nothing happens until you `start()`.

`clock_ns` is the clock period. `uio` sets the baud divider: **`clk_per_bit = uio * 4`**, so the
default 8 gives 32 — fast enough that tests finish, slow enough that the UART is comfortably
inside spec.

The object also exposes hierarchical handles that reach past the pins, into the design:
`sp.chip` (the TinyTapeout wrapper), `sp.sys` (`simproc_system`), `sp.cpu` (the core), `sp.ram`
(the 64-byte array), `sp.rf` (the four registers). A real chip has no such thing; a simulation
does, and refusing to use it out of purity costs you an afternoon per bug.

### `await sp.start(fill=FILLER)`

Starts the clock, resets the chip, writes `fill` into all 64 bytes of RAM, and starts the
background UART receiver. **Call this first, always.**

```python
sp = SimProc(dut, clock_ns=10, uio=8)
await sp.start()
```

```
clock period 10 ns; uio=8 so clk_per_bit=32
after start(): PC= 0  r0=  0 r1=  0 r2=  0 r3=  0  N=0 Z=0  IDLE
RAM filler is 0x0C, RAM depth is 64, the parking instruction is 0xF1 = JMP   -1
```

The filler matters. `0x0C` is an unimplemented opcode — three cycles, PC+1, no state change —
so a program that runs off its own end walks harmlessly through filler. Without it, unwritten
RAM reads `XXXXXXXX` under Icarus, the core decodes X, and you get a hang with no error message
at all.

### `await sp.reset()`

Pulses `rst_n` low for 10 cycles. **Clears the registers, the PC and the flags — and not the
RAM.** `dp_ram` has no reset, so whatever you loaded survives.

```python
sp.poke(0, 0x5A)
await sp.reset()
```

```
after reset(): PC= 0  r0=  0 r1=  0 r2=  0 r3=  0  N=0 Z=0  IDLE, and mem[0] is still 0x5A
```

That asymmetry is what lets you load a program, reset the core, and run from a known state.

### `await sp.set_baud(uio)`

Changes the divider mid-test; `clk_per_bit` becomes `uio * 4`. The chip reads it off `uio_in`
every cycle so it takes effect immediately, and the harness's own receiver follows along.

```python
await sp.set_baud(16)                    # clk_per_bit = 64
```

```
set_baud(16): clk_per_bit is now 64; uart_ping() -> 0xAA
```

**A parametric design that is only ever tested at its default parameter has been tested at one
point of a range.** One of the thirteen bugs is invisible at the default and at nothing else.

---

## The backdoor

`poke`/`peek`/`load` write and read the RAM array directly, in zero simulated time. The UART
path does the same job through the actual pins, at 1,104 clock cycles per command. **Use the
backdoor for setup; use the UART when the UART is what you are testing.**

### `sp.poke(addr, value)` · `sp.peek(addr)`

One byte each way. `peek` returns an `int`, or raises `ValueError` if the byte contains an X.
Both raise `IndexError` outside 0–63.

```python
sp.poke(0x30, 0xA5)
dut._log.info(f"... -> 0x{sp.peek(0x30):02X}   <- the OLD value")
await RisingEdge(dut.clk)
dut._log.info(f"one clock later, peek(0x30) -> 0x{sp.peek(0x30):02X}")
```

```
poke(0x30, 0xA5), peek(0x30) in the same instant -> 0x0C   <- the OLD value
one clock later, peek(0x30) -> 0xA5
```

> ⚠ **Read that twice.** `poke()` writes a simulator signal, and a signal written at time *T* is
> not readable until the simulator has stepped. Read it back in the same instant and you get the
> **old** value, with no error and no warning. `load()` ends with two clock cycles for exactly
> this reason; a bare `poke()` does not. **Put a trigger between a poke and the peek that checks
> it.**

Out of range:

```
poke(64, 0) raises: address 64 (0x40) is outside SimProc's 64-byte RAM. The hardware
addresses it with 8 bits but only has 64 entries, so on real silicon this read returns X
and this write is dropped. Verilator's linter says so statically; Icarus only shows it at
run time. See Lab 2.
```

### `await sp.load(program, at=0, park=True)`

Writes a list of instruction bytes into memory and **returns the parking address**.

```python
park = await sp.load([ORI(5), ADD(1, 0)])
```

```
load() put the program at 0..1 and the parking loop at 2 (0xF1 = JMP   -1)
```

Unless you pass `park=False`, it also writes one `JMP -1` — a jump to itself — immediately after
your last instruction. **You need that**, because there is no way to stop this processor after
exactly *N* instructions: `HALT` arrives over the UART and takes 1,104 clock cycles, during
which the core keeps running. So programs park themselves, the way real bare-metal test code
does, and `run()` watches for the parking address.

Does not reset the core and does not start it. Takes 2 clock cycles.

### `sp.memory(lo=0, hi=64)`

A dict of RAM contents, for dumping when something has already gone wrong. A byte containing an
X comes back as the string `'XXXXXXXX'` rather than raising — a dump you print *because*
something failed should not itself blow up on the interesting entry.

```
memory(0, 8) minus the filler: 0:0x2F 1:0x44 2:0xF1
```

---

## Reading the machine

Every one of these is synchronous — no `await`, no simulated time.

| call | returns | example |
|---|---|---|
| `sp.reg(i)` | one register as an `int` | `200` |
| `sp.regs()` | all four as a tuple | `(200, 200, 0, 0)` |
| `sp.pc()` | the program counter | `6` |
| `sp.flags()` | `(N, Z)` | `(1, 0)` |
| `sp.fsm()` | the core's state, as a name | `IDLE` |
| `sp.halt` | the `halt` pin, as a character | `'1'` |
| `sp.done` | the `done` pin, as a character | `'0'` |
| `sp.snapshot()` | `(regs, pc, N, Z)` | `((200, 200, 0, 0), 6, 1, 0)` |
| `sp.describe()` | one line of everything | `PC= 6  r0=200 r1=200 r2=  0 r3=  0  N=1 Z=0  IDLE` |

Three notes worth having before you need them.

**`halt` and `done` are characters, not integers.** `'0'`, `'1'` or `'x'`. That is on purpose:
`int()` on a value containing X raises `ValueError` in cocotb 2.x, and a test that dies with a
stack trace has told you something real in the worst possible way.

**`snapshot()` is the shape `Golden.snapshot()` returns**, so the two compare with `==` and
nothing else. That is the whole interface to model-based checking.

**`describe()` belongs in every failure message you write.** One call, every register, both
flags, the PC and the state.

### `bit(signal, index)`

Free function. One bit of any signal, as the character `'0'`, `'1'`, `'x'` or `'z'`. Use it
instead of `(int(sig.value) >> i) & 1` on anything a broken design might drive to X.

```python
dut._log.info(f"bit(dut.uo_out, 0) -> '{bit(dut.uo_out, 0)}'")
```

```
bit(dut.uo_out, 0) -> '1'  (the UART TX pin, idle high)
```

---

## Making it go

SimProc has exactly two ways to execute anything, and they are not interchangeable.
**RUN** free-runs until you send `HALT` — fast, but you cannot stop after exactly *N*
instructions. **STEP** executes one instruction and drops back to IDLE — exact, and costs a
whole UART command per instruction.

### `await sp.run(program=None, at=0, timeout_cycles=20000)` → cycles

The call you will use most. Loads, parks, starts, and watches the fetch address until it arrives
at the parking loop. Pass `program=None` to run something you loaded earlier.

```python
cycles = await sp.run([ORI(5), ADD(1, 0)])
```

```
run([ORI(5), ADD(1,0)]) -> 9 cycles, r1 = 5   (ORI is 5, ADD is 4)
```

**The returned count is exact and hand-checkable**: the clocks between fetching your first
instruction and fetching the parking loop, which is the sum of your program's instruction times
and nothing else.

On a timeout it raises with a diagnosis rather than a number:

```
the program did not reach its parking loop at address N within 20000 clock cycles.
  IDLE means the core never started. A PC far past your program means it ran off the end —
  check your branch displacements. A PC that is not moving means an infinite loop you did
  not intend.
```

### `await sp.step(n=1)`

Executes exactly `n` instructions, one `STEP` command each, coming to rest in IDLE after every
one. This is the mode for inspecting state after each instruction.

```python
await sp.load([ORI(1), ORI(2), ORI(4)])
await sp.set_pc(0)
await sp.step(1)
await sp.step(2)
```

```
after step(1):  r0 = 5, PC = 1, state IDLE
after step(2) more: r0 = 7, PC = 3
```

(`r0` starts at 5 from the previous `run()` — `step()` does not reset anything, which is the
point of it.)

### `await sp.run_cycles(n)`

Free-runs while **counting** `n` clock cycles of execution. The count starts at the first
instruction fetch, not when the `RUN` command was sent. Use it when the question is about time
rather than about the answer: *"after 40 clocks, how far has it got?"*

```python
await sp.load([ORI(1), ORI(2), ORI(4), ORI(8)])
await sp.set_pc(0)
await sp.run_cycles(10)
```

```
after run_cycles(10): r0 = 15, PC = 4
```

> ⚠ **It counts `n` cycles. It does not freeze the machine after them.** When the count is
> reached the harness sends `HALT`, and `HALT` is a UART command in flight — the core keeps
> executing until it arrives. Measured, on 40 unimplemented opcodes (3 cycles each, no parking
> loop):
>
> ```
> same call on a program that does NOT park: PC = 20.
> ```
>
> Ten clocks of three-cycle instructions is `PC = 3`, and at the instant the count reached ten
> the PC **was** 3. By the time the core came to rest it was 20. If you need the state at cycle
> *n* exactly, read it inside a watcher of your own — copy `_go()` — or give the program a
> parking loop and use `run()`. `test_api_tour.py`'s `a04` measures both.

### `await sp.set_pc(addr)` · `start_running()` · `stop_running()`

The three raw controls. `set_pc` only takes effect while the core is in IDLE. `start_running`
sends `RUN`; `stop_running` sends `HALT` and takes effect when the current instruction retires.

**If you write your own free-running measurement, start your monitor before `start_running()`.**
The chip acts on `RUN` **57 clock cycles** before `uart_cmd` returns — measured, in
[`test_handshake_timing.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_handshake_timing.py)
— so a monitor started afterwards has already missed about fourteen instructions. Every counting
call in the harness goes through one four-line helper, `_go()`, for exactly this reason. Copy
it.

---

## Protocol counters

These check the **handshake** rather than the data. A core can compute every right answer and
still get its handshake wrong, and two of the thirteen bugs do exactly that.

### `await sp.count_done_pulses(cycles)` → count

Runs the loaded program and counts rising edges of `done` over the first `cycles` clocks of
execution. `done` should pulse once per retired instruction.

```python
await sp.load([ORI(1), ADD(1, 0), SUB(2, 2), NAND(3, 3)])
await sp.set_pc(0)
pulses = await sp.count_done_pulses(17)          # 5 + 4 + 4 + 4
```

```
count_done_pulses(17) over 4 instructions -> 4
```

Instructions with an unimplemented opcode never pulse it, so keep those out of a program you are
counting — or use them on purpose to check that:

```
two unimplemented opcodes, 6 clocks -> 0 done pulses: 0x0C retires nothing
```

> **Why this matters more than it looks.** If your scoreboard is triggered by `done`, a missing
> pulse does not make your test fail — it makes your test quietly stop *scoring*. Which is
> worse.

### `await sp.count_halt_cycles(cycles)` → count

How many of the first `cycles` clocks of execution had `halt` high. While `RUN` is asserted the
answer must be **zero**.

```
count_halt_cycles(17) -> 0   (a running core must never be in IDLE)
```

A core that blips back into IDLE between instructions still computes every right answer, and is
still wrong.

---

## The wire

The harness contains a **bus functional model** (BFM): Python that pretends to be the device on
the other end of the serial line. It knows the protocol — 8N1, one low start bit, eight data
bits least-significant first, one high stop bit — and nothing else about the design.

The receiver runs as a **background task**, started by `start()`, watching `uo_out[0]` from
before the first command goes out. It has to: the chip can begin its reply while the harness is
still finishing the last stop bit of the command, and a receiver that only starts looking
afterwards does not get an error, it gets a plausible wrong byte.

| call | what it does | replies? |
|---|---|---|
| `await sp.uart_ping()` | `PING`, returns the reply | yes, `0xAA` |
| `await sp.uart_read(addr)` | `READ`, returns the byte | yes |
| `await sp.uart_write(addr, data)` | `WRITE` | no |
| `await sp.uart_get_pc()` | `GET_PC`, returns the PC | yes |
| `await sp.uart_cmd(cmd, addr=0, data=0)` | any command, no reply waited for | — |
| `await sp.send_byte(value)` | one raw 8N1 frame **plus the mandatory idle gap** | — |
| `await sp.recv_byte(timeout_cycles=20000)` | the next byte the chip sent | — |

```python
dut._log.info(f"uart_ping()      -> 0x{await sp.uart_ping():02X}")
await sp.uart_write(0x21, 0x3C)
dut._log.info(f"... uart_read(0x21) -> 0x{await sp.uart_read(0x21):02X}")
await sp.set_pc(9)
dut._log.info(f"set_pc(9) then uart_get_pc() -> {await sp.uart_get_pc()}")
```

```
uart_ping()      -> 0xAA
uart_write(0x21, 0x3C) then uart_read(0x21) -> 0x3C
set_pc(9) then uart_get_pc() -> 9
three raw send_byte() calls -> recv_byte() 0xAA
```

Three things that will cost you an hour otherwise:

**Every command is three bytes** — `cmd`, `addr`, `data` — even when the last two are ignored.
Send two and the chip is still waiting.

**`WRITE`, `RUN`, `HALT`, `STEP` and `SET_PC` do not reply.** Asking one of those for a reply
waits forever, and `recv_byte` says so in its timeout message.

**`send_byte()` leaves one bit period of idle after the frame, and that is required, not
polite.** The chip's receiver is busy for half a bit period longer than the frame it just
received. Send the next start bit immediately and it misses it — no error, just a byte shifted
by one. [The handshake is part of the contract](guide/the-handshake-is-the-contract.md) measures
all of it.

**A working `PING` does not prove the link works.** `0xF0` already has its top bit set and
`0xAA` is a fixed pattern, so a receiver whose bit period is slightly wrong still gets both of
them right.

---

## The assembler — `simproc_asm.py`

Imports nothing. Runs at a plain Python prompt, and
`python3 simproc_asm.py 0x2F 0x44` disassembles bytes from the command line.

| helper | form | byte | disassembles as |
|---|---|---|---|
| `ORI(5)` | `R0 \|= imm5`, **always r0** | `0x2F` | `ORI   5` |
| `ADD(1, 0)` | `rA += rB` | `0x44` | `ADD   r1, r0` |
| `SUB(2, 3)` | `rA -= rB` | `0xB6` | `SUB   r2, r3` |
| `NAND(1, 1)` | `rA = ~(rA & rB)` | `0x58` | `NAND  r1, r1` |
| `SHL(0, 3)` | `rA <<= amt`, amt 0–3 | `0x3B` | `SHL   r0, 3` |
| `SHR(0, 1)` | `rA >>= amt` | `0x0B` | `SHR   r0, 1` |
| `LOAD(0, 1)` | `rA = mem[rB]` | `0x10` | `LOAD  r0, r1` |
| `STORE(1, 2)` | `mem[rB] = rA` | `0x62` | `STORE r1, r2` |
| `JMP(-1)` | signed 4-bit displacement | `0xF1` | `JMP   -1` |
| `BZ(2)` | branch if `Z` | `0x2A` | `BZ    +2` |
| `BNZ(-3)` | branch if not `Z` | `0xD9` | `BNZ   -3` |
| `BPZ(1)` | branch if `N == 0` | `0x15` | `BPZ   +1` |
| `UNIMP()` | unimplemented opcode | `0x0C` | `(unimplemented)` |

### `set_reg(reg, value)`

The instructions that put an arbitrary 0–255 byte in a register. `ORI` is the only way to get a
constant into this machine, it *ORs* rather than loads, its immediate is 5 bits, and it only
ever writes `r0`. So:

```python
listing(set_reg(1, 0xB7))
```

```
  00: 06   SUB   r0, r0
  01: B7   ORI   22
  02: 3B   SHL   r0, 3
  03: 3F   ORI   7
  04: 56   SUB   r1, r1
  05: 44   ADD   r1, r0
```

**Always 4 instructions for `r0`, always 6 for the others**, so a cycle count stays predictable.

> ⚠ `set_reg` **clobbers `N` and `Z`** — `SUB`, `ORI` and `SHIFT` all set flags. Set your
> registers up *before* a compare, never between the compare and the branch. This is the single
> most common way a flag test ends up testing `set_reg` instead of the design.

### `assemble(text, base=0)`

Write the program as text and let labels do the displacement arithmetic:

```python
prog = assemble("""
        SUB   r1, r1
top:    ORI   1
        BZ    top
        SUB   r3, r3
""")
```

```
  00: 56   SUB   r1, r1
  01: 0F   ORI   1
  02: EA   BZ    -2
  03: F6   SUB   r3, r3
```

`BZ top` became `BZ -2` without you counting anything. Branch displacements are 4-bit and
**signed**, and `assemble` raises rather than silently truncating when a label is out of reach:

```
ValueError line 12: 'BZ top': 'top' is -11 instructions away and a SimProc branch only
reaches -8..+7. Move the label closer, or JMP to a JMP.
```

### `disasm(word)` · `listing(prog, base=0)`

`disasm` turns one byte back into text; `listing` produces the address/hex/mnemonic block above.
Put a `listing()` in a log line when a test fails and you save yourself twenty minutes. Put a
`disasm()` in the failure message and the reader does not have to look anything up:
`expected 0x14, got 0x24` tells nobody anything; *"at PC 6 the core ran `ORI 4` and the model
ran `ADD r0, r1`"* tells them where to look.

---

## The golden model — `golden.py`

A second implementation of the same specification, in a language where you can see what it does.
Imports nothing; `python3 golden.py` runs a demo program on its own.

| call | what it does |
|---|---|
| `Golden(memory, pc=0)` | a machine holding a program. Pads to 64 bytes with the same `0x0C` filler the DUT gets. |
| `g.step()` | one instruction. Returns the **cycle count**, or a **string** if it cannot continue. |
| `g.run(n, stop_on_reason=True)` | `n` steps. Returns `(cycles, reason_or_None)`. |
| `g.snapshot()` | `(regs, pc, N, Z)` — the same shape `sp.snapshot()` returns |
| `g.memory(lo, hi)` | a dict, like `sp.memory()` |
| `compare_memory(model, sp, lo=0, hi=64)` | every address where they disagree, as `(addr, model, dut)` |

```python
prog = set_reg(1, 20) + set_reg(2, 6) + [SUB(1, 2), STORE(1, 2)]
g = Golden(prog + [PARK])
cycles, reason = g.run(len(prog))
await sp.run(prog)
diffs = compare_memory(g, sp)
```

```
Golden.run(14) -> 59 cycles, reason=None
Golden.snapshot() -> ((6, 14, 6, 0), 14, 0, 0)
SimProc.snapshot() -> ((6, 14, 6, 0), 14, 0, 0)
compare_memory() -> []   (an empty list is the good answer)
```

`step()` returning a *string* rather than raising is deliberate: the caller can print the
model's reason next to the DUT's state instead of catching an exception.

**And the honest limitation, which is on the model's own first page:** it has no concept of
`done`, `halt`, cycle counts or the UART. A bug in any of those is invisible to it. That is not
a flaw in model-based testing; it is why a suite needs more than one kind of test in it.

### `await trace(sp, n_instr, model=None)` → `(steps, problem)`

Single-steps `n_instr` instructions, recording the state after each. `steps` is a list of
`(index, address, instruction_word, snapshot)`. `problem` is `None`, or a **string naming the
first disagreement** with the model.

```python
steps, problem = await trace(sp, len(prog), model=g)
```

```
trace() ran 7 instructions; problem = None
   0  @00  0x06 SUB   r0, r0     regs=(0, 0, 0, 0) PC=1 N=0 Z=1
   1  @01  0x0F ORI   1          regs=(1, 0, 0, 0) PC=2 N=0 Z=0
   2  @02  0x3B SHL   r0, 3      regs=(8, 0, 0, 0) PC=3 N=0 Z=0
   3  @03  0x0F ORI   1          regs=(9, 0, 0, 0) PC=4 N=0 Z=0
   4  @04  0x44 ADD   r1, r0     regs=(9, 9, 0, 0) PC=5 N=0 Z=0
   5  @05  0x6B SHL   r1, 1      regs=(9, 18, 0, 0) PC=6 N=0 Z=0
   6  @06  0xA8 NAND  r2, r2     regs=(9, 18, 255, 0) PC=7 N=1 Z=0
```

When it does disagree, `problem` is the difference between *"something is wrong somewhere"* and:

```
instruction 19, at address 19 (0x66 = SUB   r1, r2), left the machine in a different state:
      model: r=(...) PC=... N=... Z=...
        DUT: r=(...) PC=... N=... Z=...
```

Stepping is slower than free-running — every instruction costs a whole UART command. **Use
`run()` when you want the answer and `trace()` when you want to know where it went wrong.**

---

## Constants

```python
from simproc import (MEM_DEPTH, FILLER, PARK, STATE_NAMES,
                     CMD_READ, CMD_WRITE, CMD_PING, CMD_RUN,
                     CMD_HALT, CMD_STEP, CMD_SET_PC, CMD_GET_PC)
```

| | value | |
|---|---|---|
| `MEM_DEPTH` | `64` | `dp_ram` is 64 bytes; addresses 64–255 read X |
| `FILLER` | `0x0C` | unimplemented opcode: 3 cycles, PC+1, no `done` |
| `PARK` | `0xF1` | `JMP -1`, the parking loop |
| `CMD_READ` `CMD_WRITE` | `0xA3` `0x5C` | reply / no reply |
| `CMD_PING` `CMD_GET_PC` | `0xF0` `0xB2` | both reply |
| `CMD_RUN` `CMD_HALT` `CMD_STEP` `CMD_SET_PC` | `0x3F` `0xC7` `0x6D` `0x99` | none reply |
| `STATE_NAMES` | `IDLE, CYCLE_1 … CYCLE_5` | what `fsm()` indexes |

## Timing you can assert against

Deterministic; not wall clock. Every one of these is checkable in a testbench.

| instruction | cycles |
|---|---|
| `ORI` | 5 |
| `ADD` `SUB` `NAND` `SHL` `SHR` `LOAD` | 4 |
| `STORE` `JMP` `BZ` `BNZ` `BPZ` | 3 |
| an unimplemented opcode (`0xC`, `0xD`, `0xE`) | 3, and no `done` pulse |

| the UART, at the default `clk_per_bit = 32` | cycles |
|---|---|
| one 3-byte command | **1,104** = 3 × 11 × 32 + 32 + 16 |
| a command with a reply (`PING`) | 1,353 |
| loading a 64-byte program over the wire | 70,656 |
| the same program through the backdoor | 2 |
| `RUN`'s head start — the core is executing this long before `uart_cmd` returns | **57** |

## The two things that are not obvious

**`load()` writes a `JMP -1` after your program.** There is no button on this hardware that
stops it after *N* instructions. Programs park themselves, the way real bare-metal test code
does.

**A reset clears the registers and not the RAM.** That is what lets you load a program, reset
the core, and start from a known state — and it is why the random-program test in
`test_reference.py` can call `sp.reset()` between programs and still compare memory afterwards.

## Make targets

| target | what it does | wall clock |
|---|---|---|
| `make` | `sim`, then `check` | 20 s |
| `make sim` | your testbench against the golden core | ~6 s |
| `make waves` | the same run, dumping `waves.vcd` (3,007,592 bytes) | ~6 s |
| `make check` | the verdict: PASS on the good core, **FAIL on `BUG`** | ~12 s |
| `make check-all` | your testbench against all thirteen broken cores | ~77 s |
| `make bugs` | the catalogue: names, tiers, what each one teaches | instant |
| `make model` | run `golden.py` alone — no simulator involved | instant |
| `make verify` | confirm every catalogue anchor still matches `rtl/` | instant |
| `make shuttle` | the test the chip shipped with, against everything | ~16 s |

```bash
make sim   TB=test_mine          # your module instead of test_example
make check BUG=B07               # which broken core to check against
make sim   SIM=verilator         # the strict simulator
```

Wall-clock figures are **ballpark** and move by a second or two between runs. The simulated-time
numbers do not move at all, on either simulator — see
[Two simulators, two jobs](guide/two-simulators-two-jobs.md).

Next: [Output that is not an error](reference/output-that-is-not-an-error.md), for the wall of
yellow this all prints on the way past.
