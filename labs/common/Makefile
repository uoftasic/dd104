# DD104 — labs/common
#
# This directory is the shared infrastructure every lab imports.  Running
# `make` here runs the shipped example testbench against the good core and
# then against a broken one, which is both a self-test of the infrastructure
# and the shortest possible demonstration of what DD104 is about.
#
#   make            the example testbench: PASS on the good core, FAIL on B01
#   make selftest   does the grader actually grade?  (see selftest/)
#   make help       every target
#
# A lab's own Makefile is the same three lines with `COMMON := ../common`.

TB ?= test_example
include ./lab.mk

## selftest — point every checker at a deliberately broken testbench and
##            read what it says. FULL=1 also starts simulators (minutes).
.PHONY: selftest
selftest:
	@FULL=$(FULL) $(PYTHON) $(COMMON)/selftest/selftest.py
