#!/usr/bin/env python3
"""Python syntax and contributor Make targets; no Docker or external dependencies."""

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Validate the Python sources and contributor Make targets without Docker."""
    files = (
        sorted((ROOT / "bedrock_family").glob("*.py"))
        + sorted((ROOT / "scripts").glob("*.py"))
        + sorted((ROOT / "tests").glob("*.py"))
    )
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    match = re.search(
        r"^\.PHONY: (.+)$",
        (ROOT / "Makefile").read_text(encoding="utf-8"),
        re.M,
    )
    targets = {"help", "test", "lint", "verify", "docs"}
    if not match or set(match.group(1).split()) != targets:
        raise RuntimeError(
            "Make doit rester limite aux commandes de contribution."
        )
    p = subprocess.run(
        ["make", "--no-print-directory", "--dry-run", "-C", str(ROOT)]
        + sorted(targets),
        capture_output=True,
        check=False,
        text=True,
    )
    if p.returncode:
        raise RuntimeError(p.stderr or p.stdout)
    print("Python syntax: " + str(len(files)) + " files valid.")
    print("Makefile: contributor targets only; dry-run passed.")
    print("No server, Docker engine or network access used.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(1)
