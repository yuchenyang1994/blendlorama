import importlib.util
import os
import platform
import subprocess
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

LIBS_DIR = os.path.join(CURRENT_DIR, "libs")

REQUIRED_PACKAGES = ["websockets"]

if LIBS_DIR not in sys.path:
    sys.path.insert(0, LIBS_DIR)


def get_python_executable():
    executable = sys.executable
    if os.path.basename(executable).lower().startswith("python"):
        return executable
    python_home = sys.exec_prefix

    if platform.system() == "Windows":
        candidate = os.path.join(python_home, "bin", "python.exe")
        if os.path.exists(candidate):
            return candidate
        candidate = os.path.join(python_home, "python.exe")
        if os.path.exists(candidate):
            return candidate

    else:
        bin_dir = os.path.join(python_home, "bin")
        if os.path.exists(bin_dir):
            for filename in os.listdir(bin_dir):
                # 找 python3.x，排除 config 文件
                if filename.startswith("python3") and "config" not in filename:
                    return os.path.join(bin_dir, filename)

    return executable


def ensure_pip():
    python_exe = get_python_executable()
    try:
        subprocess.check_call([python_exe, "-m", "ensurepip", "--upgrade", "--user"])
        return True
    except subprocess.CalledProcessError:
        return False


def are_dependencies_installed():
    importlib.invalidate_caches()

    missing = []
    for package in REQUIRED_PACKAGES:
        if importlib.util.find_spec(package) is None:
            missing.append(package)

    return len(missing) == 0


def install_dependencies():
    if are_dependencies_installed():
        print(f"[{__package__}] Dependencies already installed.")
        return True

    print(f"[{__package__}] Installing dependencies to local library: {LIBS_DIR}")

    os.makedirs(LIBS_DIR, exist_ok=True)

    python_exe = get_python_executable()

    ensure_pip()

    cmd = (
        [
            python_exe,
            "-m",
            "pip",
            "install",
        ]
        + REQUIRED_PACKAGES
        + [
            "--target",
            LIBS_DIR,
            "--no-user",
            "--upgrade",
            "--no-cache-dir",
            "--no-warn-script-location",
        ]
    )

    try:
        subprocess.check_call(cmd)

        importlib.invalidate_caches()
        if LIBS_DIR not in sys.path:
            sys.path.insert(0, LIBS_DIR)

        print(f"[{__package__}] Installation successful!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[{__package__}] Installation failed. Error: {e}")
        return False
    except Exception as e:
        print(f"[{__package__}] Unexpected error: {e}")
        return False
