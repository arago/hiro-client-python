#
# Python executables
#
PIP := pip3
PYTHON := python3

#
# Setting path for installations as user, i.e. pip install --user ....
# For user installations, set 'export PIPARGS=--user' or execute 'make <argument> PIPARGS=--user'
#
PIPARGS ?=
export PATH := $(HOME)/.local/bin:$(PATH)

#
# GIT values
#
GIT_VERSION ?= ${shell git describe --tags --long --always}
RPM_VERSION ?= ${shell echo $(GIT_VERSION) | cut -b2- | cut -d"-" -f1}
RPM_RELEASE ?= ${shell echo $(GIT_VERSION) | cut -d"-" -f2}
IMAGE_TAG := $(if $(GIT_BRANCH),$(GIT_BRANCH),$(RPM_VERSION)_$(RPM_RELEASE))

#
# Name of the package, version and several paths of the source code
#
PACKAGENAME := hiro_graph_client

SRCPATH := src
PYTHONPATH := $(SRCPATH)/$(PACKAGENAME)
PYTHONDOCPATH := docs/python
VERSION := $(shell $(PYTHON) $(SRCPATH)/version.py)

#
# Paths and names used for distributable packages
#
DISTPATH := dist/$(VERSION)
DISTBASENAME := $(PACKAGENAME)-dist-$(VERSION)

#
# Test settings
#
TESTFILE := tests/test-results.xml


#######################################################################################################################
# Install as a local tool on the current system. Remember to use PIPARGS=--user for a local installation.
#######################################################################################################################
install:
	$(PIP) install $(PIPARGS) $(SRCPATH)/
	touch install


#######################################################################################################################
# Execute test using pytest
#######################################################################################################################
test:
	$(PIP) install $(PIPARGS) pytest
	export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m pytest -s --junitxml=$(TESTFILE)


#######################################################################################################################
# Create source code documentation using python sphinx
#######################################################################################################################

install-sphinx:
	$(PIP) install $(PIPARGS) sphinx sphinx-rtd-theme
	touch install-sphinx

# Create a python code documentation using sphinx
pythondoc: install install-sphinx
	sphinx-apidoc -f -P -o $(PYTHONDOCPATH)/hiro_graph_client $(PYTHONPATH)
	sphinx-build -M html $(PYTHONDOCPATH)/hiro_graph_client $(PYTHONDOCPATH)/hiro_graph_client


#######################################################################################################################
# Cleanup
#######################################################################################################################

# Uninstall hiro-client
uninstall:
	$(PIP) uninstall -y hiro-client $(PACKAGENAME)

# Cleanup pythondoc
clean-pythondoc:
	rm -rf $(PYTHONDOCPATH)/$(PACKAGENAME)/html $(PYTHONDOCPATH)/$(PACKAGENAME)/doctrees
	rm -f `find $(PYTHONDOCPATH) -type f \( -name "*.rst" -and -not -name "index.rst" \)`

# Cleanup, but keep installed packages and dist tar
clean:
	rm -f depends install install-sphinx
	rm -f $(TESTFILE)
	(cd $(PYTHONPATH); rm -f *.whl)
	rm -rf $(SRCPATH)/dist/ $(SRCPATH)/build/

# Like 'clean', but also remove installed packages.
distclean: uninstall clean clean-pythondoc
	rm -rf dist $(AWS_PACKAGEPATH)
	rm -f $(DISTBASENAME).tar.gz $(DISTBASENAME).zip $(S3_BUCKET_PACKAGE)
