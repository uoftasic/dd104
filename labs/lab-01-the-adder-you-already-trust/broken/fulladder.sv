// One bit of a ripple-carry adder — the DD102 finale, one slice.
module fulladder (
    input  logic a, b, cin,
    output logic sum, cout
);
    assign sum  = a ^ b ^ cin;
    assign cout = (a & b) | (cin & (a ^ b));
endmodule
