# The SimProc instruction set

This page answers: *what does every opcode do, how is it encoded, and how many cycles does it
take?*

Keep it open in a tab while you work. For the machine explained rather than tabulated, see
[SimProc in one page](../guide/simproc-in-one-page.md).

Everything here can be checked against two shipped files, the assembler
[`labs/common/simproc_asm.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/simproc_asm.py)
and the model
[`labs/common/golden.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/golden.py),
and both run at a plain Python prompt with no simulator.

## Encoding

Every instruction is one byte. Three field layouts share the space:

```
    register form     A A B B o o o o      rA = instr[7:6]   rB = instr[5:4]
                      7 6 5 4 3 2 1 0      op = instr[3:0]

    branch form       d d d d o o o o      d  = instr[7:4], 4-bit SIGNED
                      7 6 5 4 3 2 1 0      op = instr[3:0]

    SHIFT             A A D S S 0 1 1      D  = instr[5]: 1 = left, 0 = right
                      7 6 5 4 3 2 1 0      SS = instr[4:3], the amount, 0..3

    ORI               i i i i i 1 1 1      i  = instr[7:3], a 5-bit immediate
                      7 6 5 4 3 2 1 0
```

`SHIFT` and `ORI` are selected by their low three bits, not four. Everything else is selected by
the low nibble.

## The table

`rA` is both a source and the destination. Flags are `N` (bit 7 of the result) and `Z` (the
whole result was zero); a dash means the instruction leaves both exactly as they were.

| op | byte | mnemonic | what it does | flags | cycles | assembler |
|---|---|---|---|---|---|---|
| `0000` | `0x?0` | `LOAD rA, rB` | `rA <- mem[rB]`; rB is the pointer | — | 4 | `LOAD(1, 2)` |
| `0001` | `0x?1` | `JMP d` | `PC <- PC+1+d`, always | — | 3 | `JMP(-3)` |
| `0010` | `0x?2` | `STORE rA, rB` | `mem[rB] <- rA`; same order as `LOAD` | — | 3 | `STORE(1, 3)` |
| `0011` | `0x?3` | `SHL rA, n` / `SHR rA, n` | `rA <- rA << n` or `rA >> n`, `n` in 0..3 | `N Z` | 4 | `SHL(0, 3)` |
| `0100` | `0x?4` | `ADD rA, rB` | `rA <- rA + rB`, wraps at 8 bits | `N Z` | 4 | `ADD(1, 0)` |
| `0101` | `0x?5` | `BPZ d` | if `N == 0`: `PC <- PC+1+d` | — | 3 | `BPZ(2)` |
| `0110` | `0x?6` | `SUB rA, rB` | `rA <- rA - rB`, wraps at 8 bits | `N Z` | 4 | `SUB(1, 2)` |
| `0111` | `0x?7` | `ORI imm5` | `r0 <- r0 \| imm5`; always r0 | `N Z` | 5 | `ORI(5)` |
| `1000` | `0x?8` | `NAND rA, rB` | `rA <- ~(rA & rB)` | `N Z` | 4 | `NAND(1, 1)` |
| `1001` | `0x?9` | `BNZ d` | if `Z == 0`: `PC <- PC+1+d` | — | 3 | `BNZ(-3)` |
| `1010` | `0x?A` | `BZ d` | if `Z == 1`: `PC <- PC+1+d` | — | 3 | `BZ(1)` |
| `1011` | `0x?B` | *(`SHIFT` again)* | the second encoding of `SHIFT` | `N Z` | 4 | |
| `1100` | `0x?C` | *(unimplemented)* | `PC+1`, nothing else | — | 4 | `UNIMP()` |
| `1101` | `0x?D` | *(unimplemented)* | `PC+1`, nothing else | — | 4 | |
| `1110` | `0x?E` | *(unimplemented)* | `PC+1`, nothing else | — | 4 | |
| `1111` | `0x?F` | *(`ORI` again)* | the second encoding of `ORI` | `N Z` | 5 | |

`?` is whatever the register or displacement fields happen to be. The byte `0x44` is
`ADD r1, r0`; the byte `0x04` is `ADD r0, r0`; both are `ADD`.

### All 256 bytes

Every byte decodes to something. There are no illegal encodings and no opcode collisions, verified
by single-stepping all 256 instruction bytes and classifying each by cycle count, `done`, PC delta,
register write and memory write:

| | encodings | which |
|---|---|---|
| the nine 4-bit opcodes | 16 each, 144 total | `0x?0` `0x?1` `0x?2` `0x?4` `0x?5` `0x?6` `0x?8` `0x?9` `0x?A` |
| `SHIFT` | 32 | `0x?3` and `0x?B` |
| `ORI` | 32 | `0x?7` and `0x?F` |
| unimplemented | 48 | `0x?C` `0x?D` `0x?E` |
| | 256 | |

`SHIFT` and `ORI` are chosen by three bits, so each owns two low nibbles. Nothing else is assigned
to `0x?B` or `0x?F`, so the aliasing is harmless, but it does mean the byte `0xF1` is a `JMP` while
`0xFF` is an `ORI`, and the difference is one bit that most people don't look at.

## Disassembling a byte from the command line

The assembler is also a disassembler. When a test fails and a log line shows a hex byte, this is
the quickest way to find out what it was:

```bash
cd labs/common
python3 simproc_asm.py 0x2F 0x44 0xD9
```

```
0x2F   ORI   5
0x44   ADD   r1, r0
0xD9   BNZ   -3
```

It imports nothing, needs no simulator, and takes as many bytes as you give it.

Some bytes worth recognising on sight:

| byte | | |
|---|---|---|
| `0x0C` | `(unimplemented)` | what the harness fills unwritten RAM with |
| `0xF1` | `JMP -1` | the parking loop — a jump to itself |
| `0x06` | `SUB r0, r0` | the idiom for "clear `r0`" |
| `0x2F` | `ORI 5` | |
| `0x3B` | `SHL r0, 3` | |
| `0x8B` | `SHR r2, 1` | note the nibble: `SHIFT`'s second encoding |

## Branch displacements

The PC is incremented during `CYCLE_1`, *before* the branch computes its target in `CYCLE_3`.
So the displacement is measured from the instruction **after** the branch:

$$\text{target} = (\text{address of the branch}) + 1 + d$$

| | |
|---|---|
| `JMP(0)` | falls through to the next instruction |
| `JMP(1)` | skips one instruction |
| `JMP(-1)` | an infinite loop on itself — the parking idiom |
| range | `-8` to `+7`, and nothing else |

The field is four bits and it is **signed**. A branch to a label further away than that is a
hard error in the assembler, not a silent wrap:

```
ValueError: line 12: 'BNZ loop': 'loop' is -11 instructions away and a SimProc
branch only reaches -8..+7. Move the label closer, or JMP to a JMP.
```

## Flags

| set `N` and `Z` | leave them alone |
|---|---|
| `ADD` `SUB` `NAND` `SHL` `SHR` `ORI` | `LOAD` `STORE` `JMP` `BZ` `BNZ` `BPZ` |

`N` is bit 7 of the result. `Z` is "the whole 8-bit result was zero". There is no carry and no
overflow — arithmetic wraps silently.

Branches leaving the flags alone is a specified property, not an accident: it is what lets you
compare once and branch on the result twice.

```
        SUB   r1, r1        # r1 = 0  ->  Z = 1
        BZ    taken         # taken
        ORI   16            # skipped
taken:  BNZ   wrong         # must NOT be taken: Z is still 1
```

## Idioms

This instruction set lacks several things you are used to, and each absence has a standard
workaround. These are the only way to write each operation, not tricks.

| you want | you write | why |
|---|---|---|
| clear `rX` | `SUB rX, rX` | there is no `MOV` and no `CLR` |
| `NOT rX` | `NAND rX, rX` | there is no `NOT` |
| compare `rA` against `rB` | `SUB rA, rB` | there is no `CMP`, and the compare destroys `rA` |
| stop the program | `JMP -1` | there is no `HALT` instruction |
| a constant in `r0` | `SUB r0, r0`, then `ORI` | `ORI` only *sets* bits |
| a constant larger than 31 | `ORI` the high bits, `SHL`, `ORI` the low bits | the immediate is 5 bits |
| a constant in `r1`/`r2`/`r3` | build it in `r0`, then `SUB rX, rX ; ADD rX, r0` | `ORI` only writes `r0` |

> Every row in that table is also an entry in the bug catalogue. `SUB rX, rX` is symmetric, so it
> is correct on a core whose subtract is backwards. `NAND rX, rX` is the one operand pattern where
> `NAND` and `NOR` agree. The idiom a programmer reaches for first is the one that hides the bug.
> [Where bugs hide](../guide/where-bugs-hide.md) is the long version.

The assembler has a helper for building constants, because it is easy to get wrong by hand:

```python
>>> from simproc_asm import set_reg, listing
>>> print(listing(set_reg(1, 0xB7)))
  00: 06   SUB   r0, r0
  01: B7   ORI   22
  02: 3B   SHL   r0, 3
  03: 3F   ORI   7
  04: 56   SUB   r1, r1
  05: 44   ADD   r1, r0
```

It is always four instructions for `r0` and six for `r1`–`r3`, so the cycle count stays
predictable. It clobbers `N` and `Z`, because `SUB`, `ORI` and `SHL` all set flags, so set your
registers up before a compare, never between the compare and the branch.

## Cycle counts

The core is not pipelined and nothing is speculative, so a program's cycle count is the sum of
its instructions' and you can check it by hand.

| instruction | cycles | |
|---|---|---|
| `ORI` | 5 | `IDLE`→`CYCLE_1`…`CYCLE_5` |
| `ADD` `SUB` `NAND` `SHL` `SHR` `LOAD` | 4 | write-back in `CYCLE_4` |
| `STORE` `JMP` `BZ` `BNZ` `BPZ` | 3 | retires in `CYCLE_3` |
| `0xC` `0xD` `0xE` | 4 | and no `done` pulse; see below |

A branch costs 3 cycles whether or not it is taken.

> ### Unimplemented opcodes: four cycles
>
> They match no clause in `CYCLE_3`, so the FSM takes its default exit to `IDLE`, spends a cycle
> there, and is sent back to `CYCLE_1` by `run`, which is still asserted. Measured on four filler
> bytes: 16 clock cycles, 0 `done` pulses, and `halt` high on 4 of the 16.
>
> The last figure matters. `0x0C` is what `sp.start()` fills unwritten RAM with, so a program that
> runs off its own end makes the `halt` pin blink, and "`halt` must stay low while `run` is
> asserted" is an assertion [Lab 05](../labs/lab-05-every-answer-is-right-overview.md) asks you to
> write. That is your test working correctly on a machine behaving as designed.
>
> `golden.py` said three until somebody measured it; [The golden model](../guide/the-golden-model.md)
> tells the story.

## Writing a program

Three ways, from least to most readable:

```python
prog = [0x2F, 0x44, 0xD9]              # ... which of these is the loop?
```

```python
from simproc_asm import ORI, ADD, STORE
prog = [ORI(5), ADD(1, 0), STORE(1, 2)]
```

```python
from simproc_asm import assemble
prog = assemble("""
        ORI   5              # r0 = 5
        ADD   r1, r0         # r1 = 5
loop:   SUB   r1, r0         # r1 -= 5
        BNZ   loop           # ... until it hits zero
        STORE r1, r2
""")
```

The text front end does the displacement arithmetic for you. That is the only reason to use it,
and a good one, because almost everybody measures branch displacements from the wrong place the
first time.

`listing(prog)` prints an address/hex/mnemonic dump. Put it in a failure message and you save
yourself twenty minutes:

```
  00: 06   SUB   r0, r0
  01: 0F   ORI   1
  02: A6   SUB   r2, r2
```

## Traps

Each of these has cost somebody an evening.

1. `ORI` ORs. It never clears. `SUB r0, r0` first, or you get the OR of everything `r0` has
   ever held.
2. `ORI` always writes `r0`. There is no register field to get wrong, and no way to make it write
   anything else.
3. Shift amounts are 0–3. `SHL(0, 4)` raises instead of truncating quietly:
   `shift amount 4 does not fit in 2 bits. SimProc shifts by 0, 1, 2 or 3 — to shift by 4, use
   two instructions.`
4. The branch range is `-8` to `+7`, measured from the instruction after the branch.
5. Arithmetic wraps and nothing tells you. `200 + 60` is `4`, and there is no carry flag to check.
6. Addresses above 63 do not exist. Reads return `X`, writes are dropped, and neither aliases into
   low memory.
7. `LOAD rA, rB` and `STORE rA, rB` take the data register first and the pointer second. The order
   is the same for both, and it is the opposite of what many readers expect.
8. `SUB` is your compare, and it destroys `rA`. If you need the value afterwards, copy it first,
   and remember that copying costs two instructions and both flags.

## Links

- [SimProc in one page](../guide/simproc-in-one-page.md): the machine, the FSM, the pins, the protocol
- [The SimProc harness](../reference/the-harness-api.md): what the test harness gives you
- [`labs/common/simproc_asm.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/simproc_asm.py): this page as executable code, plus the disassembler
- [`labs/common/golden.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/golden.py): this page as a reference model
