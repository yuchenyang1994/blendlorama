import importlib
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


def install_dependencies():
    """Install missing dependencies using pip."""
    try:
        python_exe = sys.executable
        # Ensure pip is available
        subprocess.check_call([python_exe, "-m", "ensurepip"])
        # Install websockets
        subprocess.check_call(
            [python_exe, "-m", "pip", "install", "websockets", "numpy"]
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
