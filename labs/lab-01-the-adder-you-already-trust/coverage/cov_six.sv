// The same six cases, in plain SystemVerilog, for the coverage run.
//
// Note what is NOT in here: there is not one check.  It prints and moves on.
// That is deliberate.  Coverage instruments the DESIGN, so it measures what
// your stimulus reached — it cannot tell whether you looked at the answer.
// This file scores exactly what a fully-checking version of it would score.
module cov_six;
    logic [3:0] a, b, sum;
    logic       cin, cout;

    ripple4 dut (.a(a), .b(b), .cin(cin), .sum(sum), .cout(cout));

    int cases [6][3] = '{'{0,0,0}, '{2,3,0}, '{7,1,0},
                         '{15,0,0}, '{9,9,0}, '{4,4,0}};

    initial begin
        for (int i = 0; i < 6; i++) begin
            a   = 4'(cases[i][0]);
            b   = 4'(cases[i][1]);
            cin = 1'(cases[i][2]);
            #1;
            $display("%2d + %2d + %0d = %0d", a, b, cin, {cout, sum});
        end
        $finish;
    end
endmodule
