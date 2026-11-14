# Minecraft en famille - macOS / GNU Make 3.81+ / Python 3.9+
SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
DOCS_PYTHON ?= $(PYTHON)
LANGUAGE ?= en
LAN_IP ?=
EULA ?=
TIME ?=
STOP_AT ?=
PLAYER ?=
CMD ?=
FILE ?=
VALUE ?=
LEVEL ?=
MODE ?=
PERCENT ?=
CONFIRM ?= no
TIMEOUT ?= 120
READY_TIMEOUT ?= 180
TAIL ?= 100
export LANGUAGE LAN_IP EULA TIME STOP_AT PLAYER CMD FILE VALUE LEVEL MODE PERCENT CONFIRM TIMEOUT READY_TIMEOUT TAIL
TARGETS := help setup check config docker-start doctor up start apply stop down restart status logs logs-once console players xuids backup backups restore open-backups open-data edit edit-env pull update update-server version-pin allowlist-preview allowlist-sync allowlist-show allowlist-enable allowlist-disable allowlist-remove allowlist-edit allowlist-reload session session-status session-cancel session-stop session-logs session-default session-default-show session-default-reset worlds world-default cheats keep-inventory difficulty sleep sleep-one gamemode gamemode-all game-show game-apply game-defaults
.PHONY: $(TARGETS) test lint verify
$(TARGETS):
	@command -v $(PYTHON) >/dev/null || { echo "Python 3.9+ requis. See README.md."; exit 1; }
	@$(PYTHON) scripts/manage.py "$@"
test:
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -v
lint:
	@$(PYTHON) scripts/check_code.py
verify: lint test

.PHONY: docs
docs:
	@$(DOCS_PYTHON) scripts/build_docs.py
