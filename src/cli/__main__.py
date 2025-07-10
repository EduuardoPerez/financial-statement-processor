"""
Main entry point for CLI module execution.

This module enables running the CLI as a module with:
    uv run python -m cli.main
"""

from .main import main

if __name__ == "__main__":
    main()
