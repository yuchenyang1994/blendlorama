import importlib
import os
import platform
import subprocess
import sys

_dependencies_installed = False


def are_dependencies_installed():
    """Check if all dependencies are installed."""
    global _dependencies_installed
    if _dependencies_installed:
        return True

    try:
        importlib.import_module("websockets")
        _dependencies_installed = True
        return True
    except ImportError:
        return False


def get_websocket_wheel_path():
    """Get the appropriate websockets wheel file for the current platform."""
    libs_dir = os.path.join(os.path.dirname(__file__), "libs")

    system = platform.system().lower()
    machine = platform.machine().lower()
    python_version = f"{sys.version_info.major}{sys.version_info.minor}"

    # Map platform and architecture to wheel files
    if system == "windows":
        wheel_file = (
            f"websockets-15.0.1-cp{python_version}-cp{python_version}-win_amd64.whl"
        )
    elif system == "darwin":  # macOS
        if machine in ("arm64", "aarch64"):
            wheel_file = f"websockets-15.0.1-cp{python_version}-cp{python_version}-macosx_11_0_arm64.whl"
        else:
            wheel_file = f"websockets-15.0.1-cp{python_version}-cp{python_version}-macosx_10_9_x86_64.whl"

    else:  # Linux and others
        wheel_file = f"websockets-15.0.1-cp{python_version}-cp{python_version}-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl"

    wheel_path = os.path.join(libs_dir, wheel_file)

    # If the specific Python version wheel doesn't exist, fallback to cp311
    if not os.path.exists(wheel_path):
        fallback_wheel_file = wheel_file.replace(f"cp{python_version}-", "cp311-")
        wheel_path = os.path.join(libs_dir, fallback_wheel_file)
        return wheel_path if os.path.exists(wheel_path) else None


def install_dependencies():
    """Install missing dependencies using local wheel files."""
    try:
        python_exe = sys.executable

        # Get the appropriate wheel file
        wheel_path = get_websocket_wheel_path()
        if not wheel_path:
            print(
                f"Error: Could not find appropriate websockets wheel for {platform.system()} {platform.machine()}"
            )
            return False

        print(f"Installing websockets from: {wheel_path}")

        # Ensure pip is available
        subprocess.check_call([python_exe, "-m", "ensurepip"])

        # Install websockets from local wheel file
        subprocess.check_call(
            [
                python_exe,
                "-m",
                "pip",
                "install",
                wheel_path,
                "--no-deps",
                "--force-reinstall",
            ]
        )

        # After installation, re-check
        global _dependencies_installed
        importlib.invalidate_caches()
        importlib.import_module("websockets")
        _dependencies_installed = True

        return True

    except (subprocess.CalledProcessError, ImportError) as err:
        print(f"Error installing dependencies: {err}")
        return False
