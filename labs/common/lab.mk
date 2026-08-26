# DD104 — the shared lab makefile.
#
# Every DD104 lab's Makefile is three lines:
#
#     COMMON := ../common
#     TB     ?= test_lab01
#     include $(COMMON)/lab.mk
#
# and then `make` works, in a bare container, with no environment setup and no
# arguments.  Targets:
#
#     make            sim, then check — and a verdict
#     make sim        run your testbench against the good core
#     make waves      the same run, with a waveform file you can open
#     make check      the verdict: pass on the good core, FAIL on a broken one
#     make check-all  your testbench against all 13 broken cores at once
#     make bugs       what is in the bug catalogue
#     make model      run the golden model on its own — no simulator needed
#     make shuttle    the test the chip actually shipped with (see below)
#     make clean

COMMON  := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SELF    := $(abspath $(dir $(firstword $(MAKEFILE_LIST))))

TB      ?= test_example
SIM     ?= icarus
BUG     ?= B01
PYTHON  ?= python3

SIMMK   := $(MAKE) -f $(COMMON)/sim.mk COMMON=$(COMMON) TB=$(TB) SIM=$(SIM)
RULE    := ============================================================

.PHONY: all sim waves check check-all bugs model shuttle verify clean help

## all — sim, then check (this is what plain `make` runs)
all: sim check

## sim — your testbench, against the good core
sim:
	@echo "$(RULE)"
	@echo " SIM   $(TB)   against the golden core   ($(SIM))"
	@echo "$(RULE)"
	@$(SIMMK) sim SIM_BUILD=$(SELF)/build/sim COCOTB_RESULTS_FILE=$(SELF)/build/results.xml
	@echo ""
	@echo "   the golden core: PASS.  That is half a verdict — run 'make check'"
	@echo "   to find out whether your testbench can also FAIL."

## waves — the same run, dumping waves.vcd
waves:
	@echo "$(RULE)"
	@echo " WAVES $(TB)"
	@echo "$(RULE)"
	@$(SIMMK) sim SIM_BUILD=$(SELF)/build/waves \
	          COCOTB_RESULTS_FILE=$(SELF)/build/results-waves.xml \
	          COCOTB_PLUSARGS=+WAVES
	@echo ""
	@echo "   wrote $(SELF)/waves.vcd"
	@echo "   open it with:   surfer waves.vcd      (or: gtkwave waves.vcd)"
	@echo "   A whole processor is a lot of signals. Start with clk, uo_out,"
	@echo "   then open tb > ...simproc > U1 > CPU1 and add curr_state."

## check — the verdict mechanism
check:
	@$(PYTHON) $(COMMON)/check.py --tb $(TB) --bug $(BUG) --sim $(SIM) --dir $(SELF) || { \
	  echo ""; \
	  echo "  The verdict above is FAIL, so this target exits non-zero and make"; \
	  echo "  prints an error line under this one. That is the verdict talking,"; \
	  echo "  not a broken Makefile."; exit 1; }

## check-all — against every bug in the catalogue
check-all:
	@$(PYTHON) $(COMMON)/check.py --tb $(TB) --all --sim $(SIM) --dir $(SELF) || { \
	  echo ""; \
	  echo "  The verdict above is FAIL, so this target exits non-zero and make"; \
	  echo "  prints an error line under this one. That is the verdict talking,"; \
	  echo "  not a broken Makefile."; exit 1; }

## bugs — the catalogue, names and difficulty only
bugs:
	@$(PYTHON) $(COMMON)/bugs.py

## model — the golden model, with no simulator involved at all
model:
	@$(PYTHON) $(COMMON)/golden.py

## verify — every catalogue anchor still matches the shipped RTL
verify:
	@$(PYTHON) $(COMMON)/inject.py --verify

## shuttle — the test SimProc actually shipped with
shuttle:
	@$(PYTHON) $(COMMON)/check.py --shuttle --sim $(SIM) --dir $(SELF)

## clean — remove build/, waves and __pycache__
clean:
	rm -rf $(SELF)/build $(SELF)/waves.vcd $(SELF)/results*.xml \
	       $(SELF)/__pycache__ $(SELF)/obj_dir $(COMMON)/__pycache__
	@echo "cleaned"

## help — this list
help:
	@echo "DD104 — targets in this lab:"
	@grep -hE '^## ' $(COMMON)/lab.mk | sed 's/^## /  make /'
	@echo ""
	@echo "  variables:  TB=$(TB)   SIM=$(SIM)   BUG=$(BUG)"
