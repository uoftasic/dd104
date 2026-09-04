# DD104 — Lab 05: every answer is right and it is still broken
#
# Runs inside hpretl/iic-osic-tools:2026.08 (cocotb 2.0.1, Icarus Verilog 14.0).
# No environment setup, no arguments, no paths to retype.
#
#   make blind      the first command of this lab: an architectural testbench
#                   against BOTH broken cores, watch it pass on both
#   make new        deal a mystery core into core/
#   make hunt       your testbench against core/
#   make probe      the same run, showing everything the simulator prints
#   make verdict    the grade: golden PASS, dealt core FAIL, core/ PASS
#   make reveal     give up, and be told which bug it was
#
#   make sim        your testbench against the golden core (from ../common/lab.mk)
#   make check BUG=B08   the two-sided check against a NAMED bug, no mystery
#   make waves      the same run, dumping waves.vcd
#   make help       every target

COMMON := ../common
TB     ?= test_lab05
PYTHON ?= python3
SELF   := $(abspath .)

include $(COMMON)/lab.mk

VERBOSE ?=

.PHONY: new hunt probe verdict reveal blind

## blind — an architecturally complete testbench against both bugs in this lab
blind:
	@echo "$(RULE)"
	@echo " BLIND SPOT   test_architecture.py -- ten architecturally complete"
	@echo "              tests -- against both cores in this lab's pool."
	@echo "$(RULE)"
	@$(PYTHON) $(SELF)/blind.py

## new — deal a mystery core into core/ (this deletes any core/ you have)
new:
	@$(PYTHON) $(SELF)/hunt.py new $(if $(BUGPICK),BUG=$(BUGPICK),)

## hunt — your testbench against core/, with no grade attached
hunt:
	@$(PYTHON) $(SELF)/hunt.py hunt TB=$(TB) SIM=$(SIM) VERBOSE=$(VERBOSE)

## probe — hunt, showing everything the simulator prints (print(), dut._log)
probe:
	@$(PYTHON) $(SELF)/hunt.py probe TB=$(TB) SIM=$(SIM)

## verdict — the grade
verdict:
	@$(PYTHON) $(SELF)/hunt.py verdict TB=$(TB) SIM=$(SIM) VERBOSE=$(VERBOSE) || { \
	  echo ""; \
	  echo "  The verdict above is FAIL, so this target exits non-zero and make"; \
	  echo "  prints an error line under this one. That is the verdict talking,"; \
	  echo "  not a broken Makefile."; exit 1; }

## reveal — give up
reveal:
	@$(PYTHON) $(SELF)/hunt.py reveal
