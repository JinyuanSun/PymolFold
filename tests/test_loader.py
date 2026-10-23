import ast
import subprocess
from importlib import metadata
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from packaging import version


LOADER = Path(__file__).resolve().parents[1] / "pymolfold.py"


@pytest.fixture
def loader():
    # Load just the installer functions: executing the entry script would install
    # packages and initialize a real Qt dialog at collection time.
    tree = ast.parse(LOADER.read_text(encoding="utf-8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ("get_latest_pypi_version", "ensure_package")]
    namespace = {
        "sys": SimpleNamespace(executable="/PyMOL/bin/python", version_info=(3, 10)),
        "subprocess": Mock(PIPE=subprocess.PIPE, STDOUT=subprocess.STDOUT),
        "metadata": Mock(PackageNotFoundError=metadata.PackageNotFoundError),
        "version": version,
    }
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(LOADER), "exec"), namespace)
    namespace["get_latest_pypi_version"] = Mock(return_value="0.2.13")
    return namespace


@pytest.mark.parametrize("encoding", ["utf-8", "gbk", "cp1252"])
def test_loader_survives_local_encoding(encoding):
    source = LOADER.read_text(encoding="utf-8")
    assert source.isascii(), "The downloaded loader must survive ANSI/GBK saves"
    compile(source.encode(encoding), str(LOADER), "exec")


def test_install_failure_shows_pip_output_and_stops(loader, capsys):
    loader["metadata"].version.side_effect = metadata.PackageNotFoundError
    loader["subprocess"].run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="fatal: Python.h: No such file or directory\n"
    )
    with pytest.raises(RuntimeError, match="pip"):
        loader["ensure_package"]("pymolfold")
    assert "Python.h" in capsys.readouterr().out


def test_installer_uses_pymol_interpreter(loader):
    loader["metadata"].version.side_effect = metadata.PackageNotFoundError
    loader["subprocess"].run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Successfully installed pymolfold\n"
    )
    loader["ensure_package"]("pymolfold")
    call = loader["subprocess"].run.call_args
    assert call.args[0][:3] == ["/PyMOL/bin/python", "-m", "pip"]
    assert call.kwargs["stderr"] == subprocess.STDOUT
    assert call.kwargs["errors"] == "replace"


def test_installed_package_does_not_run_pip(loader):
    loader["metadata"].version.return_value = "0.2.13"
    loader["ensure_package"]("pymolfold")
    loader["subprocess"].run.assert_not_called()


def test_unsupported_python_is_reported_before_install(loader):
    loader["sys"].version_info = (3, 9)
    with pytest.raises(RuntimeError, match="Python 3.10"):
        loader["ensure_package"]("pymolfold")
    loader["subprocess"].run.assert_not_called()
