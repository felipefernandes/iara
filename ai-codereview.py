#!/usr/bin/env python3
"""Backwards compatibility shim. Use 'python -m iara' or 'iara' instead."""
from iara.cli import main

if __name__ == "__main__":
    main()
