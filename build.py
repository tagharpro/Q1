"""Build a standalone Windows-ready Q1 Browser with PyInstaller.

Usage:
    python build.py                # creates dist/Q1Browser/
    python build.py --portable     # also creates a zip for distribution
"""
import argparse
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist", "Q1Browser")


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def build():
    if os.path.exists(DIST):
        shutil.rmtree(DIST, ignore_errors=True)

    icon = os.path.join(ROOT, "assets", "icon.ico")

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Q1Browser",
    ]
    if os.path.exists(icon):
        args += ["--icon", icon]
    args += [
        "--add-data",
        os.pathsep.join([os.path.join(ROOT, "assets"), "assets"]),
        "--collect-all",
        "PyQt6",
        "--collect-all",
        "PyQt6.QtWebEngineCore",
        "--collect-all",
        "PyQt6.QtWebEngineWidgets",
        "--hidden-import",
        "q1_browser",
        "--hidden-import",
        "q1_browser.browser_window",
        "--hidden-import",
        "q1_browser.browser_tab",
        "--hidden-import",
        "q1_browser.pages",
        "--hidden-import",
        "q1_browser.ai_panel",
        "--hidden-import",
        "q1_browser.download_center",
        "--hidden-import",
        "q1_browser.dialogs",
        "--hidden-import",
        "q1_browser.main",
        "--hidden-import",
        "q1_browser.paths",
        "--hidden-import",
        "q1_browser.settings",
        "--hidden-import",
        "q1_browser.storage",
        os.path.join(ROOT, "run.py"),
    ]
    run(args)
    return DIST


def make_portable(dist):
    zip_path = os.path.join(ROOT, "dist", "Q1Browser-Windows-Portable.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        base = os.path.basename(dist)
        for root_dir, _dirs, files in os.walk(dist):
            for name in files:
                full = os.path.join(root_dir, name)
                arc = os.path.join(base, os.path.relpath(full, dist))
                zf.write(full, arc)
    print("->", zip_path)
    return zip_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args()
    dist = build()
    if args.portable or os.environ.get("Q1_PORTABLE"):
        make_portable(dist)


if __name__ == "__main__":
    main()
