// All 512 inputs, in plain SystemVerilog, for the coverage run.
//
// cin is the INNERMOST loop on purpose.  Toggle coverage counts transitions,
// not values, so a sweep that sets cin=0 for the first 256 vectors and cin=1
// for the last 256 visits every value and still only ever toggles cin once.
// Loop order is part of your stimulus.  See `make coverage`.
module cov_all;
    logic [3:0] a, b, sum;
    logic       cin, cout;

    ripple4 dut (.a(a), .b(b), .cin(cin), .sum(sum), .cout(cout));

    initial begin
        for (int ia = 0; ia < 16; ia++)
            for (int ib = 0; ib < 16; ib++)
                for (int ci = 0; ci < 2; ci++) begin
                    a = 4'(ia); b = 4'(ib); cin = 1'(ci); #1;
                end
        $finish;
    end
endmodule
