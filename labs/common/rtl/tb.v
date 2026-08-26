// DD104 — the Verilog shell every cocotb test attaches to.
//
// cocotb needs a top-level module to reach into.  This one does two jobs and
// nothing else:
//
//   1. instantiate the chip (`tt_um_ieeeuoftasic_simproc`) and expose its pins
//      as plain regs and wires, so `dut.ui_in.value = 1` works from Python;
//   2. open a waveform file, so `make waves` has something to show you.
//
// You will not need to edit this file in any DD104 lab.  It is the same shell
// the SimProc repo ships, plus the `$dumpfile` guard.

`default_nettype none
`timescale 1ns / 1ps

module tb ();

  // Waves.  `make waves` sets +WAVES=1; `make sim` does not, and then this
  // block does nothing.  Dumping every net of a whole processor for a long
  // test is slow and produces a large file, so it is opt-in.
  initial begin
    if ($test$plusargs("WAVES")) begin
      $dumpfile("waves.vcd");
      $dumpvars(0, tb);
    end
  end

  // The chip's pins.  `reg` for things we drive from Python, `wire` for
  // things we read.
  reg        clk;
  reg        rst_n;     // ACTIVE LOW.  The wrapper does `assign rst = ~rst_n;`
  reg        ena;
  reg  [7:0] ui_in;     // ui_in[0] is the UART receive pin
  reg  [7:0] uio_in;    // clk_per_bit = uio_in * 4  (see the wrapper)
  wire [7:0] uo_out;    // uo_out[0] = uart_tx, [1] = halt, [2] = done
  wire [7:0] uio_out;
  wire [7:0] uio_oe;

  tt_um_ieeeuoftasic_simproc tt_um_ieeeuoftasic_simproc (
      .ui_in  (ui_in),
      .uo_out (uo_out),
      .uio_in (uio_in),
      .uio_out(uio_out),
      .uio_oe (uio_oe),
      .ena    (ena),
      .clk    (clk),
      .rst_n  (rst_n)
  );

endmodule
