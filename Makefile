# Contributor commands only. Runtime operations use the bedrock-family CLI.
SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
DOCS_PYTHON ?= $(PYTHON)

.PHONY: help test lint verify docs
help:
	@printf '%s\n' 'Contributor commands:' '  make test    Run offline tests' '  make lint    Check Python syntax and Make targets' '  make verify  Run lint and tests' '  make docs    Build optional PDFs'
test:
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -v
lint:
	@$(PYTHON) scripts/check_code.py
verify: lint test

docs:
	@$(DOCS_PYTHON) scripts/build_docs.py
