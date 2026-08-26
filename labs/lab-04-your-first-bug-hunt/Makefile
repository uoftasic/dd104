# DD104 — Lab 04: your first bug hunt
#
# Runs inside hpretl/iic-osic-tools:2026.04 (cocotb 2.0.1, Icarus Verilog 14.0).
# No environment setup, no arguments, no paths to retype.
#
#   make new        deal a mystery core into core/   <- start here
#   make hunt       your testbench against core/     <- the loop you live in
#   make verdict    the grade: golden PASS, dealt core FAIL, core/ PASS
#   make reveal     give up, and be told which bug it was
#
#   make sim        your testbench against the golden core (from ../common/lab.mk)
#   make check BUG=B04   the two-sided check against a NAMED bug, no mystery
#   make waves      the same run, dumping waves.vcd
#   make bugs       the catalogue: names and what each one teaches
#   make help       every target
#
# `make` on its own runs `sim` and `check` from lab.mk. The hunt is `make new`.

COMMON := ../common
TB     ?= test_lab04
PYTHON ?= python3
SELF   := $(abspath .)

include $(COMMON)/lab.mk

.PHONY: new hunt verdict reveal

## new — deal a mystery core into core/ (this deletes any core/ you have)
new:
	@$(PYTHON) $(SELF)/hunt.py new $(if $(BUGPICK),BUG=$(BUGPICK),)

## hunt — your testbench against core/, with no grade attached
hunt:
	@$(PYTHON) $(SELF)/hunt.py hunt TB=$(TB) SIM=$(SIM)

## verdict — the grade
verdict:
	@$(PYTHON) $(SELF)/hunt.py verdict TB=$(TB) SIM=$(SIM) || { \
	  echo ""; \
	  echo "  The verdict above is FAIL, so this target exits non-zero and make"; \
	  echo "  prints an error line under this one. That is the verdict talking,"; \
	  echo "  not a broken Makefile."; exit 1; }

## reveal — give up
reveal:
	@$(PYTHON) $(SELF)/hunt.py reveal
