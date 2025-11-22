import sys
import subprocess
import json
import urllib.request
from importlib import metadata
from packaging import version
from pathlib import Path


def get_latest_pypi_version(pkg_name):
    """
    Query PyPI to find the latest version of the package.
    """
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except Exception as e:
        print(f"Warning: Could not check latest version for {pkg_name}: {e}")
        return None


def ensure_package(pkg_name):
    """
    Ensure that the package is installed.
    Checks current version against PyPI latest version.
    Only installs/upgrades if necessary.
    """
    python_exe = sys.executable
    if python_exe.endswith("pythonw.exe"):
        python_exe = python_exe.replace("pythonw.exe", "python.exe")

    # 1. Get the latest version from PyPI
    latest_version_str = get_latest_pypi_version(pkg_name)

    # 2. Check current installation
    current_version_str = None
    try:
        current_version_str = metadata.version(pkg_name)
    except metadata.PackageNotFoundError:
        pass

    # 3. Determine action
    should_install = False

    if current_version_str is None:
        print(f"[{pkg_name}] Not found. Installing latest version...")
        should_install = True
    elif latest_version_str:
        # Compare versions using 'packaging.version' to handle semantic versioning correctly
        if version.parse(latest_version_str) > version.parse(current_version_str):
            print(
                f"[{pkg_name}] Found version {current_version_str}. Upgrading to {latest_version_str}..."
            )
            should_install = True
        else:
            print(f"[{pkg_name}] Version {current_version_str} is up to date.")
    else:
        # Fallback if network check fails but package exists: Do nothing or force upgrade?
        # Usually better to stay safe and do nothing if we can't verify an update exists.
        print(
            f"[{pkg_name}] Version {current_version_str} installed. Skipping update check (network issue)."
        )

    # 4. Execute Installation if needed
    if should_install:
        try:
            subprocess.check_call(
                [
                    python_exe,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    pkg_name,
                    "--index-url",
                    "https://pypi.org/simple",
                ]
            )
            print("---------------------------------------------------------------")
            print(f"SUCCESS: {pkg_name} has been updated/installed.")
            print("Please check the latest documentation and changes at:")
            print("https://github.com/JinyuanSun/PymolFold/blob/main/README.md")
            print("---------------------------------------------------------------")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install {pkg_name}. details: {e}")


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
