#!/usr/bin/env python3
"""Assemble the small, portable WebView2 Windows build of Q1 Browser.

This package uses the installed Microsoft Edge WebView2 runtime (Shipped with
Windows 11 and most Windows 10 machines) instead of Qt WebEngine, so it is
only ~20 MB and fits in one downloadable ZIP.

Usage:
  python tools/package_webview2_windows.py \
      --pyembed-dir /tmp/pyembed \
      --wheel-dir /tmp/pywinpack \
      --launcher /tmp/buildwin/Q1Browser.exe
"""
import argparse
import os
import shutil
import subprocess
import tarfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "dist", "Q1Browser-WebView2-Windows")
APP_DIR = os.path.join(OUT_DIR, "app")
RUNTIME_DIR = os.path.join(OUT_DIR, "runtime")
SITE_DIR = os.path.join(RUNTIME_DIR, "Lib", "site-packages")

PYTHON_WHEELS = []
PYTHON_PACKAGES = [
    ("pywebview", "wheel"),
    ("pythonnet", "wheel"),
    ("bottle", "wheel"),
    ("typing_extensions", "wheel"),
    ("importlib_resources", "wheel"),
    ("proxy_tools", "tar"),
]


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def extract_wheel(wheel, target):
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(target)


def find_package(pkg_dir, prefix, kind):
    for name in sorted(os.listdir(pkg_dir)):
        if kind == "wheel" and name.lower().startswith(prefix.lower()) and name.endswith(".whl"):
            return os.path.join(pkg_dir, name)
        if kind == "tar" and name.lower().startswith(prefix.lower()) and name.endswith(".tar.gz"):
            return os.path.join(pkg_dir, name)
    raise SystemExit(f"package not found: {prefix} ({kind}) in {pkg_dir}")


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
    tmp = os.path.join(ROOT, "dist", ".pyembed2")
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
    cp_dir = os.path.join(RUNTIME_DIR, "cp311")
    if os.path.isdir(cp_dir):
        for name in os.listdir(cp_dir):
            shutil.move(os.path.join(cp_dir, name), os.path.join(RUNTIME_DIR, name))
        os.rmdir(cp_dir)
    shutil.rmtree(tmp, ignore_errors=True)


def configure_pth():
    pth = os.path.join(RUNTIME_DIR, "python311._pth")
    with open(pth, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("python311.zip\n")
        fh.write(".\n")
        fh.write("Lib\\site-packages\n")
        fh.write("..\\app\n")
        fh.write("import site\n")


def install_python_packages(pkg_dir):
    shutil.rmtree(SITE_DIR, ignore_errors=True)
    os.makedirs(SITE_DIR)
    for prefix, kind in PYTHON_PACKAGES:
        path = find_package(pkg_dir, prefix, kind)
        print(f"  installing {os.path.basename(path)}")
        if kind == "wheel":
            extract_wheel(path, SITE_DIR)
        else:  # tar.gz
            tmp = os.path.join(ROOT, "dist", ".pkg")
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            with tarfile.open(path, "r:gz") as tf:
                tf.extractall(tmp)
            # Find the actual package directory (e.g. proxy_tools.
            wanted = None
            for root, _dirs, files in os.walk(tmp):
                b = os.path.basename(root)
                if b.lower() == prefix.lower() and os.path.isdir(root):
                    wanted = root
                    break
                if b.lower().startswith(prefix.lower() + "-") and os.path.isdir(root):
                    for name in os.listdir(root):
                        if name.lower() == prefix.lower():
                            wanted = os.path.join(root, name)
                            break
            if not wanted:
                raise SystemExit(f"could not locate package {prefix} in {path}")
            shutil.copytree(wanted, os.path.join(SITE_DIR, prefix), dirs_exist_ok=True)
            shutil.rmtree(tmp, ignore_errors=True)


def copy_app():
    shutil.rmtree(APP_DIR, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "windows_app"), APP_DIR)


def copy_launcher(launcher):
    if not launcher or not os.path.exists(launcher):
        raise SystemExit("launcher exe not found; build it with Zig first")
    shutil.copy2(launcher, os.path.join(OUT_DIR, "Q1Browser.exe"))


def copy_vc_runtime(vc_dir):
    """Copy MSVC runtime DLLs needed by pythonnet into the runtime folder."""
    if not vc_dir or not os.path.isdir(vc_dir):
        print("  warning: --vc-dir not provided; skipping MSVC runtime DLLs")
        return
    names = [
        "msvcp140.dll",
        "msvcp140_1.dll",
        "msvcp140_2.dll",
        "msvcp140_atomic_wait.dll",
        "msvcp140_codecvt_ids.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll",
        "vcruntime140_threads.dll",
    ]
    for name in names:
        src = os.path.join(vc_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(RUNTIME_DIR, name))
    print(f"  copied MSVC runtime DLLs from {vc_dir}")


def write_readme():
    with open(os.path.join(OUT_DIR, "README.txt"), "w", encoding="utf-8") as fh:
        fh.write(
            "Q1 Browser (WebView2 portable build)\n"
            "=====================================\n\n"
            "1. This package is the whole application. Keep the folder together.\n"
            "2. Double-click Q1Browser.exe.\n"
            "3. It uses the Microsoft Edge WebView2 runtime installed on Windows.\n"
            "   If it doesn't start, install the WebView2 Runtime from Microsoft:\n"
            "   https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
            "AI assistant:\n"
            "  Click the AI button, open Settings, and point it to an OpenAI-compatible\n"
            "  endpoint, e.g. Ollama http://127.0.0.1:11434/v1 (model llama3.2).\n\n"
            "Source: https://github.com/tagharpro/Q1\n"
        )


def make_zip():
    zip_path = os.path.join(ROOT, "dist", "Q1Browser-Windows.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root_dir, _dirs, files in os.walk(OUT_DIR):
            for name in files:
                full = os.path.join(root_dir, name)
                arc = os.path.relpath(full, os.path.dirname(OUT_DIR))
                zf.write(full, arc)
    size = os.path.getsize(zip_path)
    print(f"-> {zip_path} ({size/1024/1024:.1f} MB)")
    if size > 99 * 1024 * 1024:
        raise SystemExit("Zip is too large for a single GitHub file (>99 MB)")
    return zip_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyembed-dir", required=True)
    parser.add_argument("--wheel-dir", required=True)
    parser.add_argument("--launcher", required=True)
    parser.add_argument("--vc-dir", default=None)
    args = parser.parse_args()

    shutil.rmtree(OUT_DIR, ignore_errors=True)
    os.makedirs(OUT_DIR)
    extract_pyembed(args.pyembed_dir)
    configure_pth()
    install_python_packages(args.wheel_dir)
    copy_vc_runtime(args.vc_dir)
    copy_app()
    copy_launcher(args.launcher)
    write_readme()
    make_zip()
    print(f"Built {OUT_DIR}")


if __name__ == "__main__":
    main()
