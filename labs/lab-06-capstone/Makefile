# DD104 — Lab 06: the capstone
#
# Runs inside hpretl/iic-osic-tools:2026.08 (cocotb 2.0.1, Icarus Verilog 14.0).
# No environment setup, no arguments, no paths to retype.
#
#   make new         deal a mystery core into core/   <- one of the hard three
#   make hunt        your suite against core/
#   make probe       the same run, showing everything the simulator prints
#   make verdict     the grade for the hunt
#   make reveal      give up, and be told which bug it was
#
#   make check-all   THE CAPSTONE DELIVERABLE: your suite against all 13 cores
#   make sim         your suite against the golden core
#   make bugs        the catalogue: names and tiers only
#   make waves       the same run, dumping waves.vcd
#   make help        every target
#
# `make check-all` is the one that graduates you. Thirteen broken processors,
# and a suite that catches every one of them.

COMMON := ../common
TB     ?= test_capstone
PYTHON ?= python3
SELF   := $(abspath .)

include $(COMMON)/lab.mk

VERBOSE ?=

.PHONY: new hunt probe verdict reveal

## new — deal a mystery core into core/ (this deletes any core/ you have)
new:
	@$(PYTHON) $(SELF)/hunt.py new $(if $(BUGPICK),BUG=$(BUGPICK),)

## hunt — your suite against core/, with no grade attached
hunt:
	@$(PYTHON) $(SELF)/hunt.py hunt TB=$(TB) SIM=$(SIM) VERBOSE=$(VERBOSE)

## probe — hunt, showing everything the simulator prints (print(), dut._log)
probe:
	@$(PYTHON) $(SELF)/hunt.py probe TB=$(TB) SIM=$(SIM)

## verdict — the grade for the hunt
verdict:
	@$(PYTHON) $(SELF)/hunt.py verdict TB=$(TB) SIM=$(SIM) VERBOSE=$(VERBOSE) || { \
	  echo ""; \
	  echo "  The verdict above is FAIL, so this target exits non-zero and make"; \
	  echo "  prints an error line under this one. That is the verdict talking,"; \
	  echo "  not a broken Makefile."; exit 1; }

## reveal — give up
reveal:
	@$(PYTHON) $(SELF)/hunt.py reveal
