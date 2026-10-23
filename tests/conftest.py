"""Keep unit tests independent of a running PyMOL application."""

import sys
from types import ModuleType
from unittest.mock import Mock


pymol = ModuleType("pymol")
pymol.cmd = Mock()
pymol.cmd.auto_arg = [{}, {}]
sys.modules["pymol"] = pymol
