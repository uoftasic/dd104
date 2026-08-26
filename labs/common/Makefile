# DD104 — labs/common
#
# This directory is the shared infrastructure every lab imports.  Running
# `make` here runs the shipped example testbench against the good core and
# then against a broken one, which is both a self-test of the infrastructure
# and the shortest possible demonstration of what DD104 is about.
#
#   make          the example testbench: PASS on the good core, FAIL on B01
#   make help     every target
#
# A lab's own Makefile is the same three lines with `COMMON := ../common`.

TB ?= test_example
include ./lab.mk
