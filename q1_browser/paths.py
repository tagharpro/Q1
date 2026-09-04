"""Resource path resolution that works in source and frozen (PyInstaller) mode."""
import os
import sys

from . import __version__


def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def app_version():
    return __version__
