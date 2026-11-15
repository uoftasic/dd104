// DD104 — counter.sv with one term removed, on purpose.
//
// This is the same counter as rtl/counter.sv except for line 33, where the
// `en &` has been deleted from tc:
//
//     good:    assign tc = en & (q == 8'hFF);
//     here:    assign tc =       (q == 8'hFF);
//
// The count is still perfect.  Every value of q is right, on every cycle, from
// every starting point.  Only the flag is wrong, and only while en is low.
//
// `make broken` runs your testbench against this file.  If your testbench
// passes here, it is not testing tc.

`default_nettype none

module counter (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        en,
    input  wire        load,
    input  wire  [7:0] d,
    output logic [7:0] q,
    output wire        tc
);

    always_ff @(posedge clk) begin
        if (!rst_n)      q <= 8'h00;
        else if (load)   q <= d;
        else if (en)     q <= q + 8'd1;
    end

    assign tc = (q == 8'hFF);          // BUG: should be `en & (q == 8'hFF)`

endmodule
