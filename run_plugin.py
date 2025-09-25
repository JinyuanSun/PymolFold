from pathlib import Path
import sys


def ensure_package(pkg_name, version=None):
    import importlib.util, subprocess

    module_name = pkg_name
    if importlib.util.find_spec(module_name) is None:
        print(f"Installing {pkg_name}{'=='+version if version else ''} ...")
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                f"{pkg_name}=={version}" if version else pkg_name,
            ]
        )


ensure_package("pymolfold", "0.2.6")

import pymolfold

# Add package root to Python path
PACKAGE_ROOT = Path(__file__).parent
if str(PACKAGE_ROOT) not in sys.path:
    # OMG, have to append instead of insert here. If you test on Windows, this will overwrite the PDB module called in Torch.
    # Because PyMol itself has a PDB file, you may get "attempted relative import with no known parent package"
    sys.path.append(str(PACKAGE_ROOT))

# Initialize plugin
pymolfold.plugin.__init_plugin__()
