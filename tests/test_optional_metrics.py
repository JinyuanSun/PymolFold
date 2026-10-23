import sys

import pytest

from pymolfold import plugin


def test_missing_metrics_gives_install_hint(monkeypatch):
    monkeypatch.setitem(sys.modules, "shadowpxmeter", None)
    monkeypatch.delitem(sys.modules, "shadowpxmeter.eval", raising=False)
    with pytest.raises(ImportError, match=r"pymolfold\[metrics\]"):
        plugin.pxmeter_align("ref", "model")


def test_commands_register_without_metrics(monkeypatch):
    monkeypatch.setitem(sys.modules, "shadowpxmeter", None)
    assert plugin.__init_plugin__() is True
    registered = {call.args[0] for call in plugin.pymol_cmd.extend.call_args_list}
    assert {"esm3", "esmfold", "bfold", "pxmeter_align"} <= registered
