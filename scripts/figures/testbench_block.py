"""What a testbench is: the testbench drives the DUT, observes it and decides PASS or FAIL."""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save


TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead


def word(d, xy, text):
    """A word centred on xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP)).label(text))


d = drawing()
d.config(margin=0.3)     # a little white around the edge, so no text touches it

# The testbench: a box around everything, named at the top.
d.add(flow.Box(w=9, h=7.7).anchor("SW").at((0, 0.6)))
word(d, (4.5, 7.75), "TESTBENCH")

# drive -> DUT
word(d, (1.6, 6.6), "drive")
d.add(elm.Line().at((2.5, 6.6)).to((6.1, 6.6)))
d.add(elm.Arrow().at((6.1, 6.6)).to((6.1, 5.35)))
dut = d.add(flow.Box(w=3.4, h=1.3).anchor("center").at((6.1, 4.7)).label("DUT"))

# DUT -> observe -> decide -> PASS / FAIL
d.add(elm.Line().at(dut.S).to((6.1, 3.2)))
d.add(elm.Arrow().at((6.1, 3.2)).to((2.75, 3.2)))
word(d, (1.75, 3.2), "observe")
d.add(elm.Arrow().at((1.83, 2.8)).to((1.83, 1.95)))
word(d, (1.75, 1.6), "decide")
d.add(elm.Line().at((2.75, 1.6)).to((4.1, 1.6)))
word(d, (5.4, 1.6), "PASS / FAIL")

print(save(d, "dd104-testbench-block"))
