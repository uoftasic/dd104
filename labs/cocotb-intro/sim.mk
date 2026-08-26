# DD104 / cocotb-intro — the inner makefile: the one that starts a simulator.
#
# You will not run this directly; the Makefile next to it does, once per
# target.  It is short on purpose — this is the whole of what it takes to
# point cocotb at a Verilog file.
#
#   VERILOG_SOURCES      the RTL, absolute paths
#   COCOTB_TOPLEVEL      the HDL module cocotb attaches `dut` to
#   COCOTB_TEST_MODULES  the PYTHON module holding your @cocotb.test()s
#                        (cocotb 1.x called this MODULE — see the 2.x page)
#   SIM                  icarus (default) or verilator
#
# Everything is overridable:  make -f sim.mk sim TB=test_03_checking RTL=rtl/counter_broken.sv
#
# ⚠ When you change RTL=, change SIM_BUILD= with it.  cocotb's makefile only
#   relinks when the sources are NEWER than sim_build/sim.vvp, so a second run
#   with a different RTL= silently re-runs the FIRST design.  The Makefile next
#   to this one gives every target its own SIM_BUILD for exactly that reason:
#
#     make -f sim.mk sim TB=test_03_checking RTL=rtl/counter_broken.sv \
#          SIM_BUILD=build/broken

HERE ?= $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

TB   ?= test_01_hello
RTL  ?= $(HERE)rtl/counter.sv
SIM  ?= icarus

TOPLEVEL_LANG       ?= verilog
COCOTB_TOPLEVEL     ?= counter
COCOTB_TEST_MODULES ?= $(TB)
VERILOG_SOURCES     ?= $(RTL)

# cocotb imports COCOTB_TEST_MODULES off PYTHONPATH, so this directory has to
# be on it.  Forgetting this is the single most common "ModuleNotFoundError".
export PYTHONPATH := $(HERE):$(PYTHONPATH)

# Icarus needs -g2012 for SystemVerilog (`logic`, `always_ff`).  Without it
# you get "syntax error" on lines that are perfectly good SystemVerilog.
ifeq ($(SIM),icarus)
  COMPILE_ARGS += -g2012
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
