# DD104 — labs/cocotb-intro
#
#   make            everything, and a verdict
#   make hello      your first cocotb test                 (test_01_hello.py)
#   make triggers   clocks, resets and triggers            (test_02_triggers.py)
#   make sim        the real testbench, good counter       (test_03_checking.py)
#   make broken     the same testbench, broken counter -- must FAIL
#   make waves      a run with a waveform file to open     (test_04_waves.py)
#   make oldapi     four cocotb 1.x forms, and what each one does here
#   make nothing    a green run that tested nothing
#   make clean
#
# Runs in hpretl/iic-osic-tools:2026.08 with no environment setup:
#
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work \
#     hpretl/iic-osic-tools:2026.08 --skip bash -c 'cd /work/labs/cocotb-intro && make'

HERE   := $(abspath $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SIM    ?= icarus
PYTHON ?= python3
RUN     = $(MAKE) --no-print-directory -f $(HERE)/sim.mk HERE=$(HERE)/ SIM=$(SIM)
RULE    = ------------------------------------------------------------------------

.PHONY: all hello triggers sim broken waves oldapi nothing clean help

all:
	@$(MAKE) --no-print-directory hello
	@$(MAKE) --no-print-directory triggers
	@$(MAKE) --no-print-directory sim
	@$(MAKE) --no-print-directory broken
	@echo ""
	@echo "$(RULE)"
	@echo " VERDICT"
	@echo "$(RULE)"
	@echo "   test_03_checking.py PASSED on rtl/counter.sv"
	@echo "   test_03_checking.py FAILED on rtl/counter_broken.sv"
	@echo ""
	@echo "   Both halves matter. A testbench that only passes has not been"
	@echo "   shown to be able to fail, and a testbench that cannot fail is"
	@echo "   not evidence of anything."
	@echo "$(RULE)"

## hello — the minimal test
hello:
	@echo ""; echo "$(RULE)"; echo " make hello   test_01_hello.py on rtl/counter.sv"; echo "$(RULE)"
	@$(RUN) sim TB=test_01_hello SIM_BUILD=$(HERE)/build/hello \
	        COCOTB_RESULTS_FILE=$(HERE)/build/hello.xml

## triggers — clocks, resets, triggers
triggers:
	@echo ""; echo "$(RULE)"; echo " make triggers   test_02_triggers.py on rtl/counter.sv"; echo "$(RULE)"
	@$(RUN) sim TB=test_02_triggers SIM_BUILD=$(HERE)/build/triggers \
	        COCOTB_RESULTS_FILE=$(HERE)/build/triggers.xml

## sim — the real testbench against the good counter (must PASS)
sim:
	@echo ""; echo "$(RULE)"; echo " make sim   test_03_checking.py on rtl/counter.sv   (must PASS)"; echo "$(RULE)"
	@$(RUN) sim TB=test_03_checking SIM_BUILD=$(HERE)/build/good \
	        COCOTB_RESULTS_FILE=$(HERE)/build/good.xml

## broken — the same testbench against the broken counter (must FAIL)
broken:
	@echo ""; echo "$(RULE)"
	@echo " make broken   test_03_checking.py on rtl/counter_broken.sv   (must FAIL)"
	@echo "$(RULE)"
	@echo " Everything below is a FAILURE YOU CAUSED ON PURPOSE. Read it as"
	@echo " practice: one test fails, five pass, and the message names the"
	@echo " line of RTL to go and look at."
	@echo "$(RULE)"
	@mkdir -p $(HERE)/build
	@if $(RUN) sim TB=test_03_checking RTL=$(HERE)/rtl/counter_broken.sv \
	        SIM_BUILD=$(HERE)/build/broken \
	        COCOTB_RESULTS_FILE=$(HERE)/build/broken.xml >$(HERE)/build/broken.log 2>&1; then \
	  sed -n '/Running tests/,$$p' $(HERE)/build/broken.log; \
	  echo ""; \
	  echo "   *** test_03_checking.py PASSED on the broken counter. ***"; \
	  echo "   That is the failure. The testbench cannot see the bug."; \
	  exit 1; \
	else \
	  sed -n '/Running tests/,$$p' $(HERE)/build/broken.log | grep -v '^make'; \
	  echo ""; \
	  echo "   FAIL, as required. The testbench can tell the two counters apart."; \
	fi

## waves — a run that writes a waveform file
waves:
	@echo ""; echo "$(RULE)"; echo " make waves   test_04_waves.py, with a waveform"; echo "$(RULE)"
	@mkdir -p $(HERE)/build/waves
	@$(RUN) sim TB=test_04_waves WAVES=1 SIM_BUILD=$(HERE)/build/waves \
	        COCOTB_RESULTS_FILE=$(HERE)/build/waves.xml
	@cp $(HERE)/build/waves/counter.fst $(HERE)/counter.fst
	@fst2vcd $(HERE)/counter.fst -o $(HERE)/counter.vcd >/dev/null 2>&1 || true
	@echo ""
	@echo "   wrote  $(HERE)/counter.fst   ($$(stat -c%s $(HERE)/counter.fst) bytes)"
	@echo "   wrote  $(HERE)/counter.vcd   ($$(stat -c%s $(HERE)/counter.vcd) bytes)"
	@echo ""
	@echo "   Open it (inside the container, on the noVNC desktop):"
	@echo "       surfer counter.fst"
	@echo "       gtkwave counter.fst"
	@echo "   Add clk, rst_n, en, load, q, tc -- in that order -- and zoom to"
	@echo "   the time the log printed next to '<-- zoom here'."

## oldapi — four cocotb 1.x forms, each in a complete file under oldapi/
oldapi:
	@echo ""; echo "$(RULE)"
	@echo " make oldapi   what cocotb 1.x code does under cocotb 2.0.1"
	@echo "$(RULE)"
	@mkdir -p $(HERE)/build
	@for t in test_1x_units test_1x_fork test_1x_assign test_1x_imports; do \
	  echo ""; \
	  echo "  ─── oldapi/$$t.py ───────────────────────────────────────────"; \
	  $(RUN) sim TB=$$t HERE=$(HERE)/oldapi/ RTL=$(HERE)/rtl/counter.sv \
	        SIM_BUILD=$(HERE)/build/$$t COCOTB_RESULTS_FILE=$(HERE)/build/$$t.xml \
	        >$(HERE)/build/$$t.log 2>&1 || true; \
	  if grep -q 'Running tests' $(HERE)/build/$$t.log; then \
	    sed -n '/Running tests/,$$p' $(HERE)/build/$$t.log | grep -v '^make' | head -40; \
	  else \
	    echo "  (this one never reached 'Running tests' -- it failed while cocotb was"; \
	    echo "   still importing the file, so no test ran at all)"; \
	    sed -n '/^Traceback/,$$p' $(HERE)/build/$$t.log | grep -v '^make' | head -24; \
	  fi; \
	done
	@echo ""
	@echo "$(RULE)"
	@echo "  Read those four results in order. The first one PASSED."
	@echo "  That is the one to be afraid of."
	@echo "$(RULE)"

## nothing — a green run that tested nothing
nothing:
	@echo ""; echo "$(RULE)"
	@echo " make nothing   COCOTB_TESTCASE naming a test that does not exist"
	@echo "$(RULE)"
	@mkdir -p $(HERE)/build
	@$(RUN) sim TB=test_03_checking COCOTB_TESTCASE=chekcing \
	        SIM_BUILD=$(HERE)/build/nothing \
	        COCOTB_RESULTS_FILE=$(HERE)/build/nothing.xml 2>&1 | tail -12
	@echo ""
	@echo "   exit status $$?, no FAIL anywhere, and zero tests ran."
	@echo "   'my tests pass' and 'my tests ran' are different claims."

## clean — remove build products
clean:
	rm -rf $(HERE)/build $(HERE)/counter.fst $(HERE)/counter.vcd \
	       $(HERE)/__pycache__ $(HERE)/oldapi/__pycache__ $(HERE)/results.xml \
	       $(HERE)/.pytest_cache $(HERE)/obj_dir
	@echo "cleaned"

## help — this list
help:
	@echo "DD104 / cocotb-intro:"
	@grep -hE '^## ' $(HERE)/Makefile | sed 's/^## /  make /'
