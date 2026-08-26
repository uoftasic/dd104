// 4-bit ripple-carry adder built from four full adders.
//
// DELIBERATELY BROKEN, and not hidden: the carry-in is dropped on the way into
// slice 0.  You are allowed to read this file.  Lab 01 is not a bug hunt — it
// is about the testbench that does or does not notice, and the hunt starts in
// Lab 04.
module ripple4 (
    input  logic [3:0] a, b,
    input  logic       cin,
    output logic [3:0] sum,
    output logic       cout
);
    logic [4:0] c;
    assign c[0] = 1'b0;              // <-- was: assign c[0] = cin;
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : slice
            fulladder fa (.a(a[i]), .b(b[i]), .cin(c[i]),
                          .sum(sum[i]), .cout(c[i+1]));
        end
    endgenerate
    assign cout = c[4];
endmodule
