"""
DD104 — the bug catalogue.

Thirteen one-line edits to `rtl/simproc_system.sv`.  Each one produces a core
that is wrong in a specific, findable way, and **all thirteen pass the test the
chip actually shipped with.**  That is the course's whole argument in one
sentence: the only test this processor has, passes on a version whose SUB is
backwards.

Each entry is `(line_number, exact_text_that_must_be_there, replacement)`.
`inject.py` checks the "must be there" text before it changes anything, so if
the RTL ever drifts the catalogue fails loudly instead of quietly producing a
core with no bug in it — a broken grader that says PASS is worse than no
grader.

You are not meant to read the right-hand column before you have hunted for the
bug.  `make bugs` prints the names and difficulty only.  If you want the
answer, it is right here, and reading it costs you the lab.
"""

# Line numbers are into rtl/simproc_system.sv, which is the upstream file at
# commit 1d97772 with two comments rewritten (see rtl/README.md).  The line
# COUNT is unchanged, so these are also the upstream line numbers.

BUGS = {

    # ── Tier 1 — findable with a unit test of the ALU alone ──────────────────

    "B01_sub_operands_swapped": dict(
        tier=1, hides_behind="SUB rX, rX — the idiom for 'clear a register'",
        edits=[(811, "            SUB:        ALUout = A - B;",
                     "            SUB:        ALUout = B - A;")]),

    "B02_nand_is_nor": dict(
        tier=1, hides_behind="NAND rX, rX — the only way to write NOT",
        edits=[(813, "            NAND:       ALUout = ~(A & B);",
                     "            NAND:       ALUout = ~(A | B);")]),

    "B03_zero_flag_low_nibble": dict(
        tier=1, hides_behind="every test that checks results and not flags",
        edits=[(822, "    assign Z = ~(|ALUout);",
                     "    assign Z = ~(|ALUout[3:0]);")]),

    # ── Tier 2 — decode and the register file ───────────────────────────────

    "B04_alu_writeback_reg_field": dict(
        tier=2, hides_behind="any instruction where rA and rB are the same register",
        edits=[(648, "                    rf_reg_w_in     = instr_reg_out[7:6];",
                     "                    rf_reg_w_in     = instr_reg_out[5:4];")]),

    "B06_shift_amount_one_bit": dict(
        tier=2, hides_behind="shifting by 1, which is what everybody writes",
        edits=[(579, "                    alu_in_b        = {6'b0, instr_reg_out[4:3]};",
                     "                    alu_in_b        = {7'b0, instr_reg_out[3]};")]),

    "B07_load_address_from_ra": dict(
        tier=2, hides_behind="LOAD rX, rX — loading through a pointer into itself",
        edits=[(589, "                    mem_addr        = reg_b_out;",
                     "                    mem_addr        = reg_a_out;")]),

    # ── Tier 3 — control flow ────────────────────────────────────────────────

    "B05_branch_offset_zero_extended": dict(
        tier=3, hides_behind="forward branches, which are all correct",
        edits=[(621, "                    alu_in_b        = {{4{instr_reg_out[7]}}, instr_reg_out[7:4]};",
                     "                    alu_in_b        = {4'b0, instr_reg_out[7:4]};")]),

    "B09_branch_clobbers_flags": dict(
        tier=3, hides_behind="using each compare exactly once",
        edits=[(622, "                    alu_op          = ALU_ADD;",
                     "                    alu_op          = ALU_ADD;\n"
                     "                    flag_wr         = 1;")]),

    # ── Tier 4 — every answer is right and it is still broken ────────────────

    "B08_store_drops_done": dict(
        tier=4, hides_behind="checking values instead of the handshake",
        edits=[(602, "                    done            = 1;",
                     "                    done            = 0;")]),

    "B13_store_falls_to_idle": dict(
        tier=4, hides_behind="the results being identical — it costs one cycle",
        edits=[(603, "                    if (run)",
                     "                    if (0)")]),

    # ── Tier 5 — the hard end ────────────────────────────────────────────────

    "B10_ori_adds_instead_of_ors": dict(
        tier=5, hides_behind="ORing in bits that were not already set — ADD agrees",
        edits=[(678, "                    alu_op          = ALU_OR;",
                     "                    alu_op          = ALU_ADD;")]),

    "B11_ori_writes_r1_reads_r0": dict(
        tier=5, hides_behind="reset — the FIRST ORI of any program is correct",
        edits=[(689, "                    rf_reg_w_in     = 2'b0;",
                     "                    rf_reg_w_in     = 2'b1;")]),

    "B12_uart_rx_bit_period": dict(
        tier=5, hides_behind="the default baud rate, where it is invisible",
        edits=[(1014, "                    if (clkCount < clk_per_bit - 1) begin",
                      "                    if (clkCount < clk_per_bit) begin")]),
}

TIER_NAMES = {
    1: "the ALU, on its own",
    2: "decode and the register file",
    3: "control flow",
    4: "protocol, not data",
    5: "the hard end",
}

# What each bug is *for*, in one line.  Safe to read — none of these says
# which line to change.
TEACHES = {
    "B01_sub_operands_swapped":
        "the number is the diagnostic: 65,024 of 65,536 vectors wrong has a shape",
    "B02_nand_is_nor":
        "'I tested NAND' and 'I tested NAND on two different values' are different sentences",
    "B03_zero_flag_low_nibble":
        "flags are architectural state; a value-only test cannot see this at all",
    "B04_alu_writeback_reg_field":
        "two nearly identical code paths, one of them wrong",
    "B06_shift_amount_one_bit":
        "sweep the field, do not sample it",
    "B07_load_address_from_ra":
        "aliasing hides bugs — make every operand distinct on purpose",
    "B05_branch_offset_zero_extended":
        "sign extension is a silent half of the number line, and it is the half you test second",
    "B09_branch_clobbers_flags":
        "'the compare is still valid' is an assumption, and assumptions get tested",
    "B08_store_drops_done":
        "if your scoreboard triggers on `done`, this does not fail your test — it silently stops it scoring",
    "B13_store_falls_to_idle":
        "functional equivalence is not correctness",
    "B10_ori_adds_instead_of_ors":
        "the wrong operator that agrees with the right one on every value you would naturally pick",
    "B11_ori_writes_r1_reads_r0":
        "a bug that a reset hides",
    "B12_uart_rx_bit_period":
        "a parametric design needs its parameter swept, not sampled at the default",
}


def names():
    """Catalogue names, in tier order."""
    return sorted(BUGS, key=lambda k: (BUGS[k]["tier"], k))


def resolve(name):
    """Accept 'B01' as shorthand for the full name.  Raise a useful error."""
    if name in BUGS:
        return name
    matches = [k for k in BUGS if k.upper().startswith(name.upper())]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise KeyError(f"no bug named {name!r}. Known bugs:\n  " + "\n  ".join(names()))
    raise KeyError(f"{name!r} matches {len(matches)} bugs: {', '.join(matches)}")


if __name__ == "__main__":
    print("DD104 bug catalogue — 13 injections, all of which pass test/test.py\n")
    for tier in sorted(TIER_NAMES):
        print(f"  Tier {tier} — {TIER_NAMES[tier]}")
        for name in names():
            if BUGS[name]["tier"] != tier:
                continue
            print(f"    {name}")
            print(f"        hides behind : {BUGS[name]['hides_behind']}")
            print(f"        teaches      : {TEACHES[name]}")
        print()
