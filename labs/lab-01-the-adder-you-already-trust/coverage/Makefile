# DD104 — Lab 01, the coverage add-on.
#
# The lab itself is one directory up.  This asks a different question about
# the same two stimulus sets: not "is the adder right?" but "which parts of
# it did my stimulus never move?"
#
#   make          toggle coverage for the six cases and for all 512
#   make clean
#
# Verilator only.  Icarus has no coverage instrumentation, so this is the one
# place in the early course where the strict simulator is the only one that
# can answer.

HERE   := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SRC    := $(abspath $(HERE)/../src)
PYTHON ?= python3
RULE   := ------------------------------------------------------------------

.PHONY: all clean help

## all — toggle coverage for both stimulus sets
all:
	@echo "=================================================================="
	@echo " COVERAGE   what did the stimulus actually reach?"
	@echo "=================================================================="
	@rm -rf $(HERE)/build && mkdir -p $(HERE)/build
	@cd $(HERE)/build && verilator --binary --timing -Wno-fatal \
	    --coverage-line --coverage-toggle -o covsix \
	    $(HERE)/cov_six.sv $(SRC)/ripple4.sv $(SRC)/fulladder.sv >/dev/null
	@cd $(HERE)/build && ./obj_dir/covsix >/dev/null && mv coverage.dat cov_six.dat
	@cd $(HERE)/build && rm -rf obj_dir && verilator --binary --timing -Wno-fatal \
	    --coverage-line --coverage-toggle -o covall \
	    $(HERE)/cov_all.sv $(SRC)/ripple4.sv $(SRC)/fulladder.sv >/dev/null
	@cd $(HERE)/build && ./obj_dir/covall >/dev/null && mv coverage.dat cov_all.dat
	@echo ""
	@echo "$(RULE)"
	@echo " six hand-picked cases"
	@echo "$(RULE)"
	@cd $(HERE)/build && $(PYTHON) $(HERE)/covcount.py cov_six.dat
	@cd $(HERE)/build && verilator_coverage --annotate annotated_six cov_six.dat >/dev/null
	@echo ""
	@sed -n '2,10p' $(HERE)/build/annotated_six/ripple4.sv
	@echo ""
	@echo "$(RULE)"
	@echo " all 512"
	@echo "$(RULE)"
	@cd $(HERE)/build && $(PYTHON) $(HERE)/covcount.py cov_all.dat
	@echo ""
	@echo "=================================================================="
	@echo " Coverage did not say whether the adder is right.  It said which"
	@echo " parts of it your stimulus never moved.  Different question."
	@echo "=================================================================="

## clean — remove build/
clean:
	rm -rf $(HERE)/build $(HERE)/__pycache__
	@echo "cleaned"

## help — this list
help:
	@grep -hE '^## ' $(HERE)/Makefile | sed 's/^## /  make /'
