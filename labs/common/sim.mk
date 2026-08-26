# DD104 — the inner makefile: this is the one that actually starts a simulator.
#
# You will not normally run this directly.  `lab.mk` calls it, and so does
# check.py, so that there is exactly ONE description of how a SimProc
# simulation is launched and nothing can drift out of step with anything else.
#
# Everything is overridable from the command line:
#
#   make -f sim.mk sim TB=test_mine RTL_DIR=../common/rtl SIM=verilator
#
# ⚠ When you change RTL_DIR=, change SIM_BUILD= with it.  cocotb's makefile only
#   relinks when the sources are NEWER than sim_build/sim.vvp, so a second run
#   against a different core silently re-runs the FIRST one.  lab.mk and
#   check.py give every run its own SIM_BUILD for exactly that reason.
#
# ── the cocotb 2.x variable names ──────────────────────────────────────────
# COCOTB_TEST_MODULES  is what 2.x calls the module holding your @cocotb.test()
#                      functions.  In 1.x it was MODULE.  MEASURED on cocotb
#                      2.0.1: MODULE still works through cocotb's own makefiles
#                      -- they map it and print
#                        "Using MODULE is deprecated, please use
#                         COCOTB_TEST_MODULES instead."
#                      -- but the mapping lives in the makefiles, so anything
#                      that bypasses them (the Python runner, pytest, a
#                      hand-written vvp line) reads only COCOTB_TEST_MODULES
#                      and ignores MODULE entirely.  Write the new name.
#                      For a green run that really did test nothing, see
#                      COCOTB_TESTCASE with a typo in it:
#                        WARNING cocotb.regression  No tests left after
#                                                   filtering with: chekcing$
#                      -- no results table, exit 0, six <skipped/> in the XML.
# COCOTB_TOPLEVEL      is 2.x for TOPLEVEL.  Both still work in 2.0.1; the new
#                      names are used here because they are the ones that will
#                      still be right next year.

COMMON  ?= $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
RTL_DIR ?= $(COMMON)/rtl
TB      ?= test_example
SIM     ?= icarus

TOPLEVEL_LANG   ?= verilog
TOPLEVEL        ?= tb
VERILOG_SOURCES ?= $(RTL_DIR)/tt_um_ieeeuoftasic_simproc.sv \
                   $(RTL_DIR)/simproc_system.sv \
                   $(RTL_DIR)/tb.v

COCOTB_TEST_MODULES ?= $(TB)

# Where the test modules and the harness live.  cocotb imports COCOTB_TEST_MODULES
# from PYTHONPATH, so both the lab directory and common/ have to be on it.
export PYTHONPATH := $(CURDIR):$(COMMON):$(PYTHONPATH)

# Icarus needs -g2012 for the SystemVerilog in this design (always_comb,
# always_ff, logic, packed structs).  Without it you get a wall of
# "syntax error" on lines that are perfectly good SystemVerilog.
ifeq ($(SIM),icarus)
  COMPILE_ARGS += -g2012
endif

# Verilator: the design does not lint clean, and that is a lesson, not an
# accident (Lab 2).  -Wno-fatal turns its 12 warnings into warnings instead of
# a refusal to build, so the simulation still runs.
ifeq ($(SIM),verilator)
  EXTRA_ARGS += -Wno-fatal
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
