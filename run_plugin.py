from pathlib import Path
import sys
import subprocess
from importlib import metadata


def ensure_package(pkg_name):
    """
    Ensure that the package is installed. If not, install or upgrade to the latest version.
    """
    python_exe = sys.executable
    if python_exe.endswith("pythonw.exe"):
        python_exe = python_exe.replace("pythonw.exe", "python.exe")
    try:
        installed_version = metadata.version(pkg_name)
        print(f"Found {pkg_name} version {installed_version}, upgrading to latest...")
        subprocess.check_call(
            [python_exe, "-m", "pip", "install", "--upgrade", pkg_name]
        )
    except metadata.PackageNotFoundError:
        print(f"{pkg_name} not found. Installing latest version...")
        subprocess.check_call([python_exe, "-m", "pip", "install", pkg_name])


# Ensure pymolfold is installed or upgraded to latest
ensure_package("pymolfold")

import pymolfold

# Add package root to Python path
PACKAGE_ROOT = Path(__file__).parent
if str(PACKAGE_ROOT) not in sys.path:
    # OMG, have to append instead of insert here. If you test on Windows, this will overwrite the PDB module called in Torch.
    # Because PyMol itself has a PDB file, you may get "attempted relative import with no known parent package"
    sys.path.append(str(PACKAGE_ROOT))

# Initialize plugin
pymolfold.plugin.__init_plugin__()
