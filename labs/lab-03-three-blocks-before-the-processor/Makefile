# DD104 — Lab 03: three blocks before the processor
#
# Runs inside hpretl/iic-osic-tools:2026.04 (cocotb 2.0.1, Icarus Verilog 14.0).
# No environment setup, no arguments, no paths to retype.
#
#   make               pc, rf, alu, then the verdict
#   make pc            test_pc.py   against `program_counter`   (15 lines of RTL)
#   make rf            test_rf.py   against `register_file`     (30 lines)
#   make alu           test_alu.py  against `ALU`               (33 lines)
#   make check         the verdict: test_alu passes the golden ALU, FAILS on a broken one
#   make check BUG=B03 ... pick which broken ALU
#   make check-alu-bugs  all three ALU bugs at once
#   make clean
#
# The RTL under test is ../common/rtl/simproc_system.sv -- the same file the
# whole course uses.  These three modules are inside it; cocotb elaborates one
# of them as the top level and the other 1,100 lines are simply not connected
# to anything.

COMMON := $(abspath ../common)
SELF   := $(abspath .)
PYTHON ?= python3
BUG    ?= B01
TB_PC  ?= test_pc
TB_RF  ?= test_rf
TB_ALU ?= test_alu

SIMMK  := $(MAKE) -f $(COMMON)/sim.mk COMMON=$(COMMON) SIM=icarus \
                  VERILOG_SOURCES=$(COMMON)/rtl/simproc_system.sv
RULE   := ============================================================

.PHONY: all pc rf alu check check-alu-bugs clean help

## all — the three unit testbenches, then the verdict
all: pc rf alu check

## pc — program_counter: 15 lines of RTL, and every behaviour it has
pc:
	@echo "$(RULE)"
	@echo " UNIT  program_counter      test_pc.py"
	@echo "$(RULE)"
	@$(SIMMK) sim TB=$(TB_PC) TOPLEVEL=program_counter \
	   SIM_BUILD=$(SELF)/build/pc COCOTB_RESULTS_FILE=$(SELF)/build/results-pc.xml

## rf — register_file: 30 lines, and three tests you write
rf:
	@echo "$(RULE)"
	@echo " UNIT  register_file        test_rf.py"
	@echo "$(RULE)"
	@$(SIMMK) sim TB=$(TB_RF) TOPLEVEL=register_file \
	   SIM_BUILD=$(SELF)/build/rf COCOTB_RESULTS_FILE=$(SELF)/build/results-rf.xml

## alu — ALU: 33 lines, 393,216 vectors, about 20 seconds
alu:
	@echo "$(RULE)"
	@echo " UNIT  ALU                  test_alu.py    (393,216 vectors, ~20 s)"
	@echo "$(RULE)"
	@$(SIMMK) sim TB=$(TB_ALU) TOPLEVEL=ALU \
	   SIM_BUILD=$(SELF)/build/alu COCOTB_RESULTS_FILE=$(SELF)/build/results-alu.xml

## check — the verdict: test_alu on the golden ALU and on one broken one
check:
	@$(PYTHON) $(SELF)/check.py one TB=$(TB_ALU) TOPLEVEL=ALU BUG=$(BUG) || { \
	  echo ""; \
	  echo "  The verdict above is FAIL, so this target exits non-zero and make"; \
	  echo "  prints an error line under this one. That is the verdict talking,"; \
	  echo "  not a broken Makefile."; exit 1; }

## check-alu-bugs — test_alu against all three bugs that live inside the ALU
check-alu-bugs:
	@$(PYTHON) $(SELF)/check.py sweep TB=$(TB_ALU) TOPLEVEL=ALU || { \
	  echo ""; \
	  echo "  The verdict above is FAIL, so this target exits non-zero and make"; \
	  echo "  prints an error line under this one. That is the verdict talking,"; \
	  echo "  not a broken Makefile."; exit 1; }

## clean — remove build/ and __pycache__
clean:
	rm -rf $(SELF)/build $(SELF)/__pycache__ $(SELF)/results*.xml
	@echo "cleaned"

## help — this list
help:
	@grep -hE '^## ' $(SELF)/Makefile | sed 's/^## /  make /'
	@echo ""
	@echo "  variables:  TB_PC=$(TB_PC)  TB_RF=$(TB_RF)  TB_ALU=$(TB_ALU)  BUG=$(BUG)"
