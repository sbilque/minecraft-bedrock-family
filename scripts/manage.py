#!/usr/bin/env python3
"""Compatibility launcher for the packaged CLI."""
from bedrock_family.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
