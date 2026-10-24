"""Check release artifacts without importing PyMOL or optional dependencies."""

from email.parser import BytesParser
from pathlib import Path
import runpy
import tarfile
import zipfile


root = Path(__file__).resolve().parents[1]
version = runpy.run_path(str(root / "pymolfold/version.py"))["__version__"]
required = {
    str(path.relative_to(root))
    for path in (root / "pymolfold").rglob("*.py")
}
required.add("pymolfold/gui/ccd_keys.json")

with tarfile.open(root / f"dist/pymolfold-{version}.tar.gz") as archive:
    prefix = f"pymolfold-{version}/"
    assert required | {"pymolfold.py"} <= {
        name.removeprefix(prefix) for name in archive.getnames()
    }
    metadata = BytesParser().parsebytes(
        archive.extractfile(prefix + "PKG-INFO").read()
    )
    assert metadata["Version"] == version

with zipfile.ZipFile(root / f"dist/pymolfold-{version}-py3-none-any.whl") as archive:
    assert required <= set(archive.namelist())
    info = f"pymolfold-{version}.dist-info/"
    wheel_metadata = BytesParser().parsebytes(archive.read(info + "METADATA"))
    assert wheel_metadata["Name"] == "pymolfold"
    assert wheel_metadata["Version"] == version
    assert wheel_metadata["Requires-Python"] == ">=3.10"
    requirements = wheel_metadata.get_all("Requires-Dist", [])
    assert requirements == metadata.get_all("Requires-Dist", [])
    assert any("shadowpxmeter" in req and 'extra == "metrics"' in req
               for req in requirements)
    assert not any("dockq" in req.lower() for req in requirements)
    entry_points = archive.read(info + "entry_points.txt").decode()
    assert "pymolfold = pymolfold.plugin:__init_plugin__" in entry_points
    assert "fold_batch" not in entry_points
    assert not any("token" in name.lower() for name in archive.namelist())

print(f"Validated sdist and wheel for pymolfold {version}")
