from pathlib import Path
import sys


def ensure_package(pkg_name, version=None):
    import importlib.util
    import subprocess
    import sys
    from importlib import metadata

    module_name = pkg_name
    python_exe = sys.executable
    if python_exe.endswith("pythonw.exe"):
        python_exe = python_exe.replace("pythonw.exe", "python.exe")
    try:
        installed_version = metadata.version(module_name)
        if version and installed_version != version:
            print(
                f"Found {pkg_name} version {installed_version}, upgrading to {version}..."
            )
            subprocess.check_call(
                [
                    python_exe,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    f"{pkg_name}=={version}",
                ]
            )
    except metadata.PackageNotFoundError:
        print(f"Installing {pkg_name}{'==' + version if version else ''}...")
        subprocess.check_call(
            [
                python_exe,
                "-m",
                "pip",
                "install",
                f"{pkg_name}=={version}" if version else pkg_name,
            ]
        )


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
