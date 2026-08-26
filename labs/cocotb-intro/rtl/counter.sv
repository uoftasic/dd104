// DD104 — the smallest DUT in the course.
//
// An 8-bit up-counter with a synchronous active-low reset, a count enable and
// a parallel load.  It exists so that the first cocotb testbench you write has
// something to talk to that fits on one screen.
//
// The pin conventions match SimProc on purpose:
//   * rst_n is ACTIVE LOW  — the counter clears when rst_n is 0
//   * reset is SYNCHRONOUS — it only takes effect on a rising clock edge
//
// tc ("terminal count") is high on the cycle where the counter is about to
// wrap: the count is 255 AND we are actually counting.

`default_nettype none

module counter (
    input  wire        clk,
    input  wire        rst_n,   // active low, synchronous
    input  wire        en,      // count enable
    input  wire        load,    // parallel load, beats en
    input  wire  [7:0] d,       // the value loaded when load is high
    output logic [7:0] q,       // the count
    output wire        tc       // 1 on the cycle before the count wraps
);

    always_ff @(posedge clk) begin
        if (!rst_n)      q <= 8'h00;
        else if (load)   q <= d;
        else if (en)     q <= q + 8'd1;
    end

    assign tc = en & (q == 8'hFF);

endmodule
