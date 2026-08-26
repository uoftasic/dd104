# verify/Makefile -- runs the systematic suite against a working copy's RTL.
#
# Called by verify/run_verification.py, which copies this file plus the
# harness next to the core under test.  Not a student-facing Makefile.
SIM ?= icarus
WAVES ?= 0
TOPLEVEL_LANG ?= verilog
CORE ?= ..
VERILOG_SOURCES = $(CORE)/src/tt_um_ieeeuoftasic_simproc.sv \
                  $(CORE)/src/simproc_system.sv \
                  $(CORE)/test/tb.v
TOPLEVEL = tb
COCOTB_TEST_MODULES ?= test_suite
SIM_BUILD ?= sim_build/$(COCOTB_TEST_MODULES)
COCOTB_RESULTS_FILE ?= results_$(COCOTB_TEST_MODULES).xml
include $(shell cocotb-config --makefiles)/Makefile.sim
