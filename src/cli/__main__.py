"""
Main entry point for CLI module execution.

This module enables running the CLI as a module with:
    uv run python -m cli
"""

import sys
from pathlib import Path

# Add src to path to avoid module import issues
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.main import main

if __name__ == "__main__":
    main()
