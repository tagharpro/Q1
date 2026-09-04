"""Q1 Browser entry point."""
import sys
import os

# Make sure the package in the repo root is importable when frozen by PyInstaller.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from q1_browser.main import main

if __name__ == "__main__":
    main()
