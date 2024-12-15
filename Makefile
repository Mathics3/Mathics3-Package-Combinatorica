# A GNU Makefile to run various tasks - compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= admin-tools/git2cl
PYTHON ?= python3
PIP ?= pip3
BASH ?= bash
RM  ?= rm
PYTEST_OPTIONS ?=
DOCTEST_OPTIONS ?=

.PHONY: \
   all \
   check \
   test

#: Default target - same as "make check"
all: check

#: Install Mathics
install:
	$(PYTHON) setup.py install

#: Run the tests
test check: pytest


#: Run pytest tests. Use environment variable "PYTEST_OPTIONS" for pytest options
pytest:
	MATHICS_CHARACTER_ENCODING="ASCII" $(PYTHON) -m pytest $(PYTEST_OPTIONS) $(PYTEST_WORKERS) test

#: Remove ChangeLog
rmChangeLog:
	$(RM) ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@
	patch -R ChangeLog < ChangeLog-spell-corrected.diff
