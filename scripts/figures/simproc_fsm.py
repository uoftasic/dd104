"""SimProc in one page: the core's six-state FSM, and the path each kind of instruction takes."""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11           # font size for the notes under the states
BOX_W, BOX_H = 2.3, 0.9
ROW = 2.35          # distance between the branch rows
BUS_X = 12.4        # the vertical line the branches leave CYCLE_3 by
COUNT_X = 21.4      # where the cycle counts end


def text(d, xy, s, halign="center", size=None):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP))
          .label(s, halign=halign, fontsize=size))


def state(d, x, y, name, w=BOX_W):
    return d.add(flow.Box(w=w, h=BOX_H).anchor("center").at((x, y)).label(name))


def note(d, box, lines, halign="center"):
    """One or more lines of small text under a state."""
    x = box.S[0] if halign == "center" else box.SW[0]
    for k, s in enumerate(lines):
        text(d, (x, box.S[1] - 0.45 - 0.45 * k), s, halign=halign, size=NOTE)


d = drawing()

# The main row: IDLE, then the three cycles every instruction goes through.
idle = state(d, 1.0, 0, "IDLE", w=1.6)
c1 = state(d, 4.6, 0, "CYCLE_1")
c2 = state(d, 7.6, 0, "CYCLE_2")
c3 = state(d, 10.6, 0, "CYCLE_3")
d.add(elm.Arrow().at(idle.E).to(c1.W).label("run", loc="top", fontsize=NOTE))
d.add(elm.Arrow().at(c1.E).to(c2.W))
d.add(elm.Arrow().at(c2.E).to(c3.W))
note(d, c1, ["fetch", "PC ← PC+1"])
note(d, c2, ["read rA,rB"])
note(d, c3, ["decode"])

# CYCLE_3 hands each instruction to one of four paths.
d.add(elm.Line().at(c3.E).to((BUS_X, 0)))
d.add(elm.Line().at((BUS_X, 0)).to((BUS_X, -3 * ROW)))

# 3 cycles: straight back to CYCLE_1.
d.add(elm.Arrow().at((BUS_X, 0)).to((BUS_X + 1.0, 0)))
text(d, (BUS_X + 1.15, 0), "back to CYCLE_1", halign="left")
text(d, (BUS_X + 1.15, -0.45 - BOX_H / 2), "STORE and all branches", halign="left", size=NOTE)
text(d, (COUNT_X, 0), "3 cycles", halign="right")

# 4 cycles: a write-back cycle.
y = -ROW
d.add(elm.Arrow().at((BUS_X, y)).to((BUS_X + 1.0, y)))
c4 = state(d, BUS_X + 1.0 + BOX_W / 2, y, "CYCLE_4")
d.add(elm.Arrow().at(c4.E).right(1.0))
c1b = state(d, c4.E[0] + 1.0 + BOX_W / 2, y, "CYCLE_1")
note(d, c4, ["write back"])
note(d, c1b, ["ADD SUB NAND", "SHL SHR LOAD"])
text(d, (COUNT_X, y), "4 cycles", halign="right")

# 5 cycles: ORI.
y = -2 * ROW
d.add(elm.Arrow().at((BUS_X, y)).to((BUS_X + 1.0, y)))
c4b = state(d, BUS_X + 1.0 + BOX_W / 2, y, "CYCLE_4")
d.add(elm.Arrow().at(c4b.E).right(1.0))
state(d, c4b.E[0] + 1.0 + BOX_W / 2, y, "CYCLE_5")
note(d, c4b, ["ORI: OR, then write r0"], halign="left")
text(d, (COUNT_X, y), "5 cycles", halign="right")

# 4 cycles: an unimplemented opcode leaves through IDLE.
y = -3 * ROW
d.add(elm.Arrow().at((BUS_X, y)).to((BUS_X + 1.0, y)))
idle_b = state(d, BUS_X + 1.0 + BOX_W / 2, y, "IDLE")
d.add(elm.Arrow().at(idle_b.E).right(1.0))
state(d, idle_b.E[0] + 1.0 + BOX_W / 2, y, "CYCLE_1")
note(d, idle_b, ["0xC 0xD 0xE"], halign="left")
text(d, (COUNT_X, y), "4 cycles", halign="right")

print(save(d, "dd104-simproc-fsm"))
