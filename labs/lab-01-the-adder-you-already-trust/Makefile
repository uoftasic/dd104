# DD104 — Lab 01: the adder you already trust
#
# Runs inside hpretl/iic-osic-tools:2026.08 (cocotb 2.0.1, Icarus Verilog 14.0).
# No environment setup, no arguments, no paths to retype.
#
#   make          sim, then check -- and a verdict
#   make sim      your testbench against src/       (the good adder)
#   make broken   your testbench against broken/    (watch it fail, on purpose)
#   make check    the verdict: pass on src/, FAIL on broken/
#   make clean

COMMON := $(abspath ../common)
SELF   := $(abspath .)
TB     ?= test_adder
PYTHON ?= python3

SIMMK  := $(MAKE) -f $(COMMON)/sim.mk COMMON=$(COMMON) TB=$(TB) SIM=icarus \
                  TOPLEVEL=ripple4
RULE   := ============================================================

.PHONY: all sim broken check clean help

## all — sim, then check (this is what plain `make` runs)
all: sim check

## sim — your testbench against the good adder in src/
sim:
	@echo "$(RULE)"
	@echo " SIM   $(TB)   against src/  (the good adder)"
	@echo "$(RULE)"
	@$(SIMMK) sim \
	   VERILOG_SOURCES="$(SELF)/src/ripple4.sv $(SELF)/src/fulladder.sv" \
	   SIM_BUILD=$(SELF)/build/sim COCOTB_RESULTS_FILE=$(SELF)/build/results.xml
	@echo ""
	@echo "   Green. That is half a verdict. 'make check' is the other half."

## broken — the same testbench against the adder that drops its carry-in
broken:
	@echo "$(RULE)"
	@echo " SIM   $(TB)   against broken/  (carry-in dropped)"
	@echo "$(RULE)"
	@$(SIMMK) sim \
	   VERILOG_SOURCES="$(SELF)/broken/ripple4.sv $(SELF)/broken/fulladder.sv" \
	   SIM_BUILD=$(SELF)/build/broken-sim \
	   COCOTB_RESULTS_FILE=$(SELF)/build/results-broken.xml

## check — the verdict: PASS on src/, FAIL on broken/
check:
	@$(PYTHON) $(SELF)/check.py $(TB) || { \
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
	@echo "  variables:  TB=$(TB)"
