"""DD104 bug catalogue for the forked SimProc core.

One entry per shipped variant.  `edits` is a list of (line, exact_old_text,
new_text) against `golden/src/simproc_system.sv` -- the line numbers are the
same ones the upstream file has at 1d97772, because the fork changed comments
only and never changed a line count.

The anchor text is asserted before every edit, so if the fork ever drifts the
catalogue fails loudly instead of quietly producing a different bug.

Which tests catch which bug is deliberately NOT recorded here -- it is a
measurement, and it lives in `verify/results.json`, written by
`verify/run_verification.py`.  `tier` and `lab` are editorial: where the bug sits
in the course, not what it does.
"""

BUGS = {
    "bug-01": dict(
        cat="B01", tier=1, lab=1,
        title="SUB computes B - A instead of A - B",
        edits=[(811, "            SUB:        ALUout = A - B;",
                     "            SUB:        ALUout = B - A;")],
    ),
    "bug-02": dict(
        cat="B02", tier=1, lab=1,
        title="NAND is wired as NOR",
        edits=[(813, "            NAND:       ALUout = ~(A & B);",
                     "            NAND:       ALUout = ~(A | B);")],
    ),
    "bug-03": dict(
        cat="B03", tier=1, lab=1,
        title="Z flag only looks at the low nibble of the result",
        edits=[(822, "    assign Z = ~(|ALUout);",
                     "    assign Z = ~(|ALUout[3:0]);")],
    ),
    "bug-04": dict(
        cat="B04", tier=2, lab=2,
        title="ALU write-back uses the rB field instead of rA",
        edits=[(648, "                    rf_reg_w_in     = instr_reg_out[7:6];",
                     "                    rf_reg_w_in     = instr_reg_out[5:4];")],
    ),
    "bug-05": dict(
        cat="B05", tier=2, lab=3,
        title="branch displacement is zero-extended, not sign-extended",
        edits=[(621, "                    alu_in_b        = {{4{instr_reg_out[7]}}, instr_reg_out[7:4]};",
                     "                    alu_in_b        = {4'b0, instr_reg_out[7:4]};")],
    ),
    "bug-06": dict(
        cat="B06", tier=2, lab=2,
        title="shift amount is taken from one bit instead of two",
        edits=[(579, "                    alu_in_b        = {6'b0, instr_reg_out[4:3]};",
                     "                    alu_in_b        = {7'b0, instr_reg_out[3]};")],
    ),
    "bug-07": dict(
        cat="B07", tier=2, lab=2,
        title="LOAD addresses memory with rA instead of rB",
        edits=[(589, "                    mem_addr        = reg_b_out;",
                     "                    mem_addr        = reg_a_out;")],
    ),
    "bug-08": dict(
        cat="B08", tier=3, lab=4,
        title="STORE never pulses done",
        edits=[(602, "                    done            = 1;",
                     "                    done            = 0;")],
    ),
    "bug-09": dict(
        cat="B09", tier=3, lab=3,
        title="a taken branch overwrites N and Z with its own PC arithmetic",
        edits=[(622, "                    alu_op          = ALU_ADD;",
                     "                    alu_op          = ALU_ADD;\n                    flag_wr         = 1;")],
    ),
    "bug-10": dict(
        cat="B10", tier=4, lab=5,
        title="ORI adds the immediate instead of ORing it",
        edits=[(678, "                    alu_op          = ALU_OR;",
                     "                    alu_op          = ALU_ADD;")],
    ),
    "bug-11": dict(
        cat="B11", tier=4, lab=5,
        title="ORI reads R0 and writes R1",
        edits=[(689, "                    rf_reg_w_in     = 2'b0;",
                     "                    rf_reg_w_in     = 2'b1;")],
    ),
    "bug-12": dict(
        cat="B12", tier=4, lab=5,
        title="UART RX bit period is one clock too long",
        edits=[(1014, "                    if (clkCount < clk_per_bit - 1) begin",
                      "                    if (clkCount < clk_per_bit) begin")],
    ),
    "bug-13": dict(
        cat="B13", tier=3, lab=4,
        title="STORE drops to IDLE for one cycle even while run is asserted",
        edits=[(603, "                    if (run)",
                     "                    if (0)")],
    ),
}

ORDER = [f"bug-{i:02d}" for i in range(1, 14)]


def apply_edits(text, name):
    """Return `text` with the named bug's edits applied.  Asserts every anchor."""
    lines = text.split("\n")
    for ln, old, new in BUGS[name]["edits"]:
        if lines[ln - 1] != old:
            raise SystemExit(
                f"{name}: anchor drift at golden/src/simproc_system.sv:{ln}\n"
                f"  file has: {lines[ln - 1]!r}\n"
                f"  expected: {old!r}\n"
                f"The fork moved under the catalogue.  Fix bugs.py, then "
                f"regenerate the patches and re-run the verification.")
        lines[ln - 1] = new
    return "\n".join(lines)
