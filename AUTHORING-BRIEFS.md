# DD104 — authoring briefs for the unwritten pages

**Not part of the course site.** These briefs were previously embedded as HTML comments inside
the stub pages under `docs/`, where docsify served them to anyone who opened the page source.
They name bugs `B01`–`B13` and describe where several of them hide, so they are spoilers.
They were moved here so a student reading a stub page cannot trip over them.

**Do not read this file if you are taking DD104.** Same rule as `labs/common/bugs.py`.

When a page is written, delete its section below.

---

## `docs/guide/directed-random-and-the-gap.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    Should I write tests by hand or generate them?

What this page must contain:
  - Both, and the page is about which bugs each one CANNOT find.
  - Directed: you choose the situation, so you can reach a corner on
    purpose - and you can only reach corners you have thought of.
  - Random: it reaches situations you did not think of, at a rate you can
    afford, and it needs a golden model because nobody can hand-check 600
    instructions.
  - THE MEASURED GAP, and it is the reason this page exists. A 20-program
    x 30-instruction random test compared instruction-by-instruction
    against golden.py - 600 random instructions - MISSES B03 (a flag bug)
    and MISSES B07 (LOAD reading through the wrong register) entirely.
    Verified. Random stimulus with no coverage model does not find a flag
    bug, and it does not find a bug that needs two operands to be
    different.
  - The fix is not more random. It is CONSTRAINED random plus a coverage
    list: bias the generator toward distinct operands, all four shift
    amounts, backward branches, and then measure whether it got there.
    Ties directly back to coverage-is-a-question.md.
  - Reproducibility: cocotb prints its seed on every run
    (`Seeding Python random module with ...`). A random failure you cannot
    replay is not a bug report. Show the real line and how to pin it.
  - Reflex rule.
  - Forward to: the-handshake-is-the-contract.md

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
```

---

## `docs/guide/flags-are-state.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    I checked the answer and it was right. What else is there to check?

What this page must contain:
  - N and Z are not debug output. They are architectural state: the only
    way this machine makes a decision, and they persist between
    instructions.
  - Measured facts to build on: N = ALUout[7], Z = ~(|ALUout), pure
    combinational functions of the result. Flags are written ONLY by
    ADD/SUB/NAND/SHIFT (CYCLE_3) and ORI (CYCLE_4); LOAD, STORE and all
    four branches leave them alone.
  - Demonstrate the value/flag split with real numbers from B03: value
    mismatches 0 EVERYWHERE, flag mismatches ADD 3840, SUB 3840, OR 255,
    NAND 255, SHL 14400, SHR 3136. Every one of those is derivable by
    hand and the derivation is the lesson - ADD/SUB is 15 nonzero results
    with a zero low nibble x 256 pairs = 3840; OR is A[3:0]=B[3:0]=0 (256
    pairs) minus the genuinely-zero case = 255. Have the student close one
    of them by hand.
  - Then the second half: a flag is only useful if it SURVIVES until the
    branch that reads it. Two branches off one compare (`BZ ...; BNZ ...`)
    is a day-one idiom and it is where B09 lives. One branch after a
    compare works perfectly.
  - The prior being overwritten: "the compare is still valid" is an
    assumption, and it is testable.
  - Reflex rule: after every operation, assert the value AND both flags;
    and test that a flag survives an instruction that should not touch it.
  - Forward to: where-bugs-hide.md

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
```

---

## `docs/guide/simproc-in-one-page.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    What is this processor, exactly? I need to know what it should do before I can say it does not.

What this page must contain:
  - The module tree: tt_um_ieeeuoftasic_simproc (pin map) ->
```

---

## `docs/guide/the-golden-model.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    The input space is too big to walk. What do I compare against instead?

What this page must contain:
  - The idea: a second, independent implementation of the SPECIFICATION,
    written in a language where it is easy to be obviously right. About 120
    lines of Python is enough for this whole ISA - labs/common/golden.py.
  - Independence is the whole value. Two implementations sharing a
    misunderstanding agree perfectly and both are wrong. Say plainly what
    the golden model does NOT protect you from.
  - Run it with no simulator at all: `make model` (MEASURED, re-run):
        16 instructions in memory, 28 executed, 109 clock cycles
        registers: r0=32 r1=15 r2=1 r3=32
        mem[0x20] = 15   (all 28 instructions executed)
  - PREDICT ->
```

---

## `docs/guide/the-handshake-is-the-contract.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    Every register, every flag and every byte of memory is correct. How can it still be broken?

What this page must contain:
  - Two of the thirteen bugs leave EVERY architectural result correct.
    B08 and B13. Registers, memory, flags, PC - all right, all the time.
    This page is why that is still a bug.
  - `done` is a one-cycle pulse per retired instruction; `halt` is high in
    IDLE. Together they are the interface between this core and anything
    that drives it. Measured: 9 instructions retired, 8 `done` pulses,
    under B08.
  - THE SHARP EDGE, and it is the best sentence on the page: if your
    scoreboard triggers on `done`, a dropped `done` does not make your
    test FAIL. It makes your test silently stop scoring. A test that stops
    checking and stays green is worse than a test that goes red.
  - B13: functionally identical output, one wasted cycle and a one-cycle
    `halt` blip per STORE. On a real chip that is a performance bug and a
    debugger-visible glitch. Only a protocol assertion sees it.
  - The harness gives you the tools: `count_done_pulses(n)`,
    `count_halt_cycles(n)`, and exact cycle counts from `sp.run()`.
  - The prior being overwritten: "functional equivalence is correctness."
    It is not. Timing and handshake are part of what you shipped.
  - Reflex rule: assert one `done` per retired instruction, and assert
    `halt` stays low for the whole time `run` is asserted.
  - Forward to: writing-the-bug-report.md

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
```

---

## `docs/guide/two-simulators-two-jobs.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    Why does this course ship two simulators, and which one should I be running?

What this page must contain:
  - Icarus is the default because of the number that matters when you are
    debugging: MEASURED, labs/common, six example tests - Icarus 7.8 s,
    Verilator 22.6 s cold (Verilator simulates faster and builds for ~15 s).
    Re-measure both before publishing.
  - Name the scary output before it appears. Icarus prints 28 `sorry:
    constant selects in always_* processes are not fully supported` notes at
    22 distinct places, every compile, exit 0, simulation correct. A real
    Icarus failure starts a line with `error:`.
  - Verilator REFUSES TO BUILD the shipped RTL: `%Error: Exiting due to 12
    warning(s)` at default, 19 with -Wall. Census: 6 WIDTHTRUNC, 4
    WIDTHEXPAND, 2 CASEINCOMPLETE; -Wall adds 4 UNUSEDSIGNAL, 1
    UNUSEDPARAM, 1 PINCONNECTEMPTY, 1 DECLFILENAME. sim.mk passes
    -Wno-fatal for exactly this reason - say so.
  - THE SET PIECE, and it is the page's whole reason to exist. Four of the
    twelve are one real finding at simproc_system.sv lines 848/851/856/857:
        %Warning-WIDTHTRUNC: Bit extraction of array[63:0] requires
                             6 bit index, not 8 bits.
    The RAM is 64 deep; the address bus is 8 bits. Verilator finds it
    STATICALLY in 0.4 s. Icarus finds it at run time, as eight X bits
    arriving on the TX pin, and only if you happen to read a high address.
    Demonstrate both halves: lint, then a UART READ of 0x45 (measured: the
    read returns X; the matching WRITE is silently dropped and does NOT
    alias into low memory - mem[0x05] is still 0x42 afterwards).
  - The prior being overwritten: "a warning is a suggestion." Here one of
    them is a real bug in the address decode of a real chip.
  - Reflex rule: lint before you simulate; an X on a pin is a question, not
    a glitch.
  - Forward to: simproc-in-one-page.md

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
```

---

## `docs/guide/where-bugs-hide.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    The bugs I am hunting are one line each. Why can I not just read the file?

What this page must contain:
  - THE THESIS: a hidden bug is not a subtle bug. It is a bug whose wrong
    behaviour AGREES with the right behaviour on exactly the inputs a
    person naturally picks. Every one of the thirteen is one line, and you
    could read all thirteen in a minute if you knew which lines to read.
  - The taxonomy, with a SimProc example each. Name the bug ID; NEVER print
    the edit.
      * SYMMETRY. A - B == B - A whenever A == B. 512 of 65,536 pairs
        survive an operand swap, and `SUB rX, rX` (clear a register) is in
        that 512. Same trap in NAND: `NAND rX, rX` is the only way to write
        NOT in this machine, and it is exactly where NAND and NOR agree
        (256 of 65,536 pairs). B01, B02.
      * ALIASING. Two operands that happen to be the same register. `LOAD
        r1, r1` - loading through a pointer into itself - is a real idiom
        and is correct under B07. The author of this course's own first
        draft of that test used it and caught nothing. TELL THAT STORY: a
        testbench author's blind spot found by injecting the bug is worth
        more than the bug.
      * THE DEFAULT VALUE. Shift by 1 is what everybody writes; shift by 2
        and 3 are where B06 lives. The UART's default baud is where B12
        does NOT live - measured: B12 is behaviourally identical to clean
        at clk_per_bit >= 32, PING still answers 0xAA at 16, nothing works
        at <= 8.
      * RESET. After reset every register is 0, so `0 | imm` and `0 + imm`
        agree, and so do "the right register" and "the wrong register".
        The FIRST instance of the instruction is always correct;
        divergence starts at the second. B10, B11.
      * ONE SIDE OF THE NUMBER LINE. Zero-extending a signed displacement
        leaves every FORWARD branch exactly right (+0..+7) and sends every
        backward branch 16 too far. "Skip the next instruction" passes;
        the first loop never terminates. B05.
      * STATE YOU FORGOT WAS STATE. Flags. Handshake pins. Cycle counts.
        Forward to flags-are-state.md and
        the-handshake-is-the-contract.md.
  - The measured punchline for the random-stimulus reader: T08's 600
    random instructions miss B03 entirely, and miss B07 entirely. Random
    without a coverage model is not a safety net.
  - Reflex rule: make every operand distinct on purpose; sweep every field;
    run each instruction TWICE.
  - Forward to: directed-random-and-the-gap.md

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
```

---

## `docs/guide/writing-the-bug-report.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    I found it. What do I actually hand to the designer?

What this page must contain:
  - The deliverable of verification is not a red test. It is a report
    someone can act on without re-deriving your week.
  - The five parts, each with a worked SimProc example:
      1. The smallest program that reproduces it. Minimise: cut
         instructions until it stops failing, then put the last one back.
      2. Expected vs actual, as numbers, with the arithmetic shown.
      3. The shape - how many vectors, and what the count implies.
      4. Where it is NOT: what still works. This is what makes a report
         credible and it is what localises the fix.
      5. The one-line reflex the test suite gained, so it never comes back.
  - Worked example end to end on one Tier-1 bug the student has already
    found by the time they read this page. Do NOT introduce a new one.
  - Regression: the report is finished when there is a test in the suite
    that fails before the fix and passes after. `make check BUG=...` is
    that, mechanised.
  - Close the course: point back at test/test.py from
    it-works-is-not-a-result.md and ask the student to write the one-line
    claim their own suite now supports. It should be an uncomfortably
    long sentence, and that is the whole point.
  - Forward to: labs/lab-06-capstone-overview.md, then DD201 and DD202.

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
```

---

## `docs/reference/output-that-is-not-an-error.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    The screen is full of red and yellow. Did something break?

What this page must contain:
  The page a student lands on at 2 a.m. Every entry: the exact text, what
  produced it, whether it matters, and the one-line rule for telling it
  apart from a real failure.
  - Icarus `sorry: constant selects in always_* processes are not fully
    supported` - 28 lines at 22 distinct places, EVERY compile, exit 0,
    simulation correct. Icarus is saying it will make the process
    sensitive to the whole vector instead of the selected bits: MORE
    sensitivity, not less. Rule: a real Icarus failure starts a line with
    `error:` and stops.
  - Verilator `%Error: Exiting due to 12 warning(s)` (19 with -Wall). Not
    a compile error - a policy. sim.mk passes -Wno-fatal. Census in
    two-simulators-two-jobs.md. But FOUR of the twelve are a real bug -
    link there, do not bury it.
  - cocotb `DeprecationWarning: The 'units' argument has been renamed to
    'unit'.` - your code is 1.x. Harmless today.
  - cocotb WARNING lines for a FAILING test: cocotb logs an assertion
    failure at WARNING level, so yellow is where your real failure is.
    Say this explicitly - students look for red.
  - `make: *** [lab.mk:64: check] Error 1` under a FAIL verdict. Correct
    and expected: the verdict exits non-zero on purpose so it is usable
    from CI. That is the verdict talking, not a broken Makefile.
  - `ValueError: Can't convert LogicArray to int: it contains non-0/1
    values` - this one IS real. It means the design put X on a pin.
  - `Could not initialize GTK!  Is DISPLAY env var/xhost set?` - GTKWave
    with no display.
  - Every entry needs a verbatim string. Do not paraphrase a tool.

Sources of truth (in this order):
  - research/verified-toolchain.md          measured tool behaviour
  - research/dd103-student-testing.md §5    the eight binding design rules
  - planning/decisions.md                   D1-D12
  - courses/dd104/labs/common/README.md     the harness, with measured numbers
  - courses/dd104/labs/common/bugs.py       the catalogue (NEVER quote answers here)
  - reference/simproc/src/simproc_system.sv the RTL itself

Binding rules for this page:
  1. Every number comes from a run you did, in
     hpretl/iic-osic-tools:2026.04, quoted to the digit. Wall-clock seconds
     are the only figures allowed to be approximate, and must be labelled so.
  2. Demonstrate failure; never assert it. Every demonstration is paired
     with a one-line reflex rule the student can carry.
  3. Any runnable thing ships in a lab package. A printed snippet is either
     a complete file, or is labelled an excerpt and names its shipped path.
  4. Name scary-but-normal output BEFORE the student sees it, with the exact
     text (Icarus `sorry:` notes, Verilator's `%Error: Exiting due to N
     warning(s)`, cocotb's `units=` DeprecationWarning).
  5. Document the dead end - the tool or command that looks official and is
     not.
  6. Name the prior this page overwrites: one sentence, before the
     demonstration, saying where the student's intuition is about to betray
     them.
  7. Never print a bug's answer. Bug identifiers (B01..B13) may be named;
     the one-line edit that causes them may not.
  8. Close by pointing forward, by page name and link.
```

---

## `docs/reference/simproc-instruction-set.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    What does every opcode do, how is it encoded, and how many cycles does it take?

What this page must contain:
  A card, not an essay. Everything here is measured, and the empirical
  classification of all 256 instruction bytes is the proof there are no
  encoding collisions.
  - Encoding layouts: register form `AA BB oooo` (rA=instr[7:6],
    rB=instr[5:4], opcode instr[3:0]); branch form `dddd oooo`; and the two
    3-LSB forms, SHIFT `AA D SS 011` and ORI `iiiii 111`, where the opcode
    is only instr[2:0] and the field grows upward.
  - The full table: opcode, mnemonic, operation, cycles, flags written.
      0000 LOAD  rA <- mem[rB]                              4   no flags
      0001 JUMP  PC <- PC+1+SE(instr[7:4])                  3   no flags
      0010 STORE mem[rB] <- rA                              3   no flags
      0011 SHIFT rA <- rA << instr[4:3] if instr[5] else >> 4   flags
      0100 ADD   rA <- rA + rB                              4   flags
      0101 BPZ   if !N: PC <- PC+1+SE(instr[7:4])           3   no flags
      0110 SUB   rA <- rA - rB                              4   flags
      0111 ORI   R0 <- R0 | ZE(instr[7:3])                  5   flags
      1000 NAND  rA <- ~(rA & rB)                           4   flags
      1001 BNZ   if !Z: PC <- PC+1+SE(instr[7:4])           3   no flags
      1010 BZ    if  Z: PC <- PC+1+SE(instr[7:4])           3   no flags
      1011 = SHIFT (3-LSB alias)                            4   flags
      1100/1101/1110 unimplemented: 3 cycles, PC+1, no state
                     change, and NO `done` pulse
      1111 = ORI (3-LSB alias)                              5   flags
  - The 256-byte classification, which is the no-collision proof: 48
    unimplemented (C,D,E), 64 branch (1,5,9,A), 16 STORE (2), 80 four-cycle
    (0,3,4,6,B), 16 NAND (8), 32 ORI (7,F). 48+64+16+80+16+32 = 256.
  - The ALU: ADD 000, SUB 001, OR 010, NAND 011, SHL 100, SHR 101; ops 6
    and 7 return 8'h00 (so N=0, Z=1 - a DEFINED answer for an undefined
    opcode). SHL/SHR shift by B[1:0]. N = result[7], Z = ~(|result). No
    carry-out, no overflow, 8-bit wrap.
  - Branch range -8..+7, target = PC_of_instruction + 1 + SE(disp).
  - The UART command table (all three bytes, always): 0xA3 READ, 0x5C
    WRITE, 0xF0 PING->
```

---

## `docs/reference/the-harness-api.md`

```
AUTHORING BRIEF — delete this comment when the page is written.

FILENAME IS FIXED. It is linked from docs/_sidebar.md, docs/README.md and
from other guide pages. Do not rename it; if the title needs to change, keep
the filename and change the heading.

Question this page answers (keep it, verbatim, as the first line):
    What can I ask the harness for, and what does it already do for me?

What this page must contain:
  Reference card for labs/common/simproc.py, simproc_asm.py and golden.py.
  The package README is the tutorial; this is the lookup table. Keep them
  consistent or delete one.
  - SimProc(dut) / await sp.start() - clock, reset, RAM blanked to 0x0C.
  - await sp.run(prog) ->
```

