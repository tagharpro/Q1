#!/usr/bin/env python3
"""Assemble a portable Windows build of Q1 Browser.

This is the build-time tool for producing the Windows release package:
  * an embedded Windows CPython runtime (python-embed wheel on PyPI),
  * the Windows PyQt6 + PyQt6-WebEngine wheels,
  * the Q1 Browser source,
  * a small native launcher (Q1Browser.exe).

Usage:
  python tools/package_windows.py --pyembed-dir /tmp/pyembed \
      --wheel-dir /tmp/qtwin --launcher /tmp/buildwin/Q1Browser.exe
"""
import argparse
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "dist", "Q1Browser-Windows")
APP_DIR = os.path.join(OUT_DIR, "app")
RUNTIME_DIR = os.path.join(OUT_DIR, "runtime")
SITE_DIR = os.path.join(RUNTIME_DIR, "Lib", "site-packages")
PYTHON_EMBED_VERSIONS = {
    "3.11.0": "python_embed-3.11.0.tar.gz",
}
QT_WHEELS = [
    "PyQt6",
    "PyQt6-Qt6",
    "PyQt6-WebEngine",
    "PyQt6-WebEngine-Qt6",
    "PyQt6-sip",
]


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def extract_wheel(wheel, target):
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(target)


def find_wheel(wheel_dir, prefix):
    norm = prefix.lower().replace("-", "_")
    for name in sorted(os.listdir(wheel_dir)):
        if not name.endswith(".whl"):
            continue
        base = name.split("-")[0].lower().replace("-", "_")
        if base == norm or base.startswith(norm):
            return os.path.join(wheel_dir, name)
    raise SystemExit(f"wheel not found for {prefix} in {wheel_dir}")


def extract_pyembed(pyembed_dir):
    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    os.makedirs(RUNTIME_DIR)
    tgz = None
    for name in os.listdir(pyembed_dir):
        if name.startswith("python_embed") and name.endswith(".tar.gz"):
            tgz = os.path.join(pyembed_dir, name)
            break
    if not tgz:
        raise SystemExit("python-embed tarball not found")
    # data.zip is inside the tarball, so extract the tarball to a temp folder.
    tmp = os.path.join(ROOT, "dist", ".pyembed")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.unpack_archive(tgz, tmp)
    data_zip = None
    for root, _dirs, files in os.walk(tmp):
        if "data.zip" in files:
            data_zip = os.path.join(root, "data.zip")
    if not data_zip:
        raise SystemExit("data.zip not found in python-embed tarball")
    with zipfile.ZipFile(data_zip) as zf:
        zf.extractall(RUNTIME_DIR)
    # The data.zip stores the interpreter under cp311/; move it up so the
    # launcher can run runtime\pythonw.exe directly.
    cp_dir = os.path.join(RUNTIME_DIR, "cp311")
    if os.path.isdir(cp_dir):
        for name in os.listdir(cp_dir):
            shutil.move(os.path.join(cp_dir, name), os.path.join(RUNTIME_DIR, name))
        os.rmdir(cp_dir)
    shutil.rmtree(tmp, ignore_errors=True)
    return tgz


def configure_pth():
    pth = os.path.join(RUNTIME_DIR, "python311._pth")
    with open(pth, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("python311.zip\n")
        fh.write(".\n")
        fh.write("Lib\\site-packages\n")
        fh.write("..\\app\n")
        fh.write("import site\n")


def extract_qt_wheels(wheel_dir):
    shutil.rmtree(SITE_DIR, ignore_errors=True)
    os.makedirs(SITE_DIR)
    for prefix in QT_WHEELS:
        wheel = find_wheel(wheel_dir, prefix)
        print(f"  extracting {os.path.basename(wheel)}")
        extract_wheel(wheel, SITE_DIR)


def copy_app():
    shutil.rmtree(APP_DIR, ignore_errors=True)
    os.makedirs(APP_DIR)
    shutil.copytree(os.path.join(ROOT, "q1_browser"), os.path.join(APP_DIR, "q1_browser"))
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(APP_DIR, "assets"))
    shutil.copy2(os.path.join(ROOT, "run.py"), os.path.join(APP_DIR, "run.py"))


def copy_launcher(launcher):
    if not launcher or not os.path.exists(launcher):
        raise SystemExit("launcher exe not found; build it with Zig first")
    shutil.copy2(launcher, os.path.join(OUT_DIR, "Q1Browser.exe"))


def write_readme():
    with open(os.path.join(OUT_DIR, "README.txt"), "w", encoding="utf-8") as fh:
        fh.write(
            "Q1 Browser (Windows portable build)\n"
            "====================================\n\n"
            "1. Double-click Q1Browser.exe.\n"
            "2. The browser uses the built-in embedded Python + PyQt6/WebEngine.\n"
            "3. Keep the whole folder together (runtime, app, Q1Browser.exe).\n\n"
            "Built-in AI assistant:\n"
            "  Settings > AI -> point to an OpenAI-compatible endpoint\n"
            "  e.g. Ollama: http://127.0.0.1:11434/v1 (model llama3.2)\n\n"
            "Source: https://github.com/tagharpro/Q1\n"
        )


def make_zip():
    zip_path = os.path.join(ROOT, "dist", "Q1Browser-Windows-Portable.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    base = os.path.basename(OUT_DIR)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root_dir, _dirs, files in os.walk(OUT_DIR):
            for name in files:
                full = os.path.join(root_dir, name)
                arc = os.path.join(base, os.path.relpath(full, OUT_DIR))
                zf.write(full, arc)
    print("->", zip_path)
    return zip_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyembed-dir", required=True)
    parser.add_argument("--wheel-dir", required=True)
    parser.add_argument("--launcher", required=True)
    args = parser.parse_args()

    shutil.rmtree(OUT_DIR, ignore_errors=True)
    os.makedirs(OUT_DIR)
    extract_pyembed(args.pyembed_dir)
    configure_pth()
    extract_qt_wheels(args.wheel_dir)
    copy_app()
    copy_launcher(args.launcher)
    write_readme()
    make_zip()
    print(f"Built {OUT_DIR}")


if __name__ == "__main__":
    main()
