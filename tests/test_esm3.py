import asyncio
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from pymolfold.predictors.esm import ESM3Predictor
from pymolfold import plugin, server
from fastapi import HTTPException


@pytest.fixture
def sdk(monkeypatch):
    # Match the public esm==3.2.1 SDK contract without loading Torch or calling Forge.
    class ESMProteinError(Exception):
        def __init__(self, error_code, error_msg):
            self.error_code = error_code
            self.error_msg = error_msg

    class ESMProtein:
        def __init__(self, sequence):
            self.sequence = sequence

    class GenerationConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    esm = ModuleType("esm")
    esm.sdk = ModuleType("esm.sdk")
    esm.sdk.api = ModuleType("esm.sdk.api")
    esm.sdk.api.ESMProtein = ESMProtein
    esm.sdk.api.ESMProteinError = ESMProteinError
    esm.sdk.api.GenerationConfig = GenerationConfig
    esm.sdk.client = Mock()
    for name, module in [("esm", esm), ("esm.sdk", esm.sdk), ("esm.sdk.api", esm.sdk.api)]:
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setenv("ESM_API_TOKEN", "test-token")
    return esm.sdk


@pytest.mark.parametrize("raised", [False, True])
def test_api_error_preserves_code_and_message(sdk, tmp_path, raised):
    error = sdk.api.ESMProteinError(401, "Invalid API token")
    generate = sdk.client.return_value.generate
    if raised:
        generate.side_effect = error
    else:
        generate.return_value = error
    with pytest.raises(RuntimeError, match=r"ESM3 API error \(401\): Invalid API token"):
        ESM3Predictor(str(tmp_path)).predict("ACDEFGHIK")
    assert list(tmp_path.iterdir()) == []


def test_successful_prediction_is_still_exported(sdk, tmp_path):
    prediction = sdk.client.return_value.generate.return_value
    prediction.to_protein_chain.return_value.to_pdb_string.return_value = "ATOM test\n"
    predictor = ESM3Predictor(str(tmp_path))
    result = predictor.predict("ACDEFGHIK", name="example", num_steps=4, temperature=0.5)
    assert result["structures"] == [{"structure": "ATOM test\n", "source": "example"}]
    assert predictor.save_structures(result, "example")[0].read_text() == "ATOM test\n"
    prompt, config = sdk.client.return_value.generate.call_args.args
    assert prompt.sequence == "ACDEFGHIK"
    assert (config.track, config.num_steps, config.temperature) == ("structure", 4, 0.5)


def test_cli_reports_api_error_without_loading_a_structure(sdk, tmp_path, monkeypatch, capsys):
    sdk.client.return_value.generate.return_value = sdk.api.ESMProteinError(
        403, "Model access denied"
    )
    monkeypatch.setattr(plugin, "ABS_PATH", str(tmp_path))
    plugin.pymol_cmd.load.reset_mock()
    plugin.query_esm3("ACDEFGHIK", name="example")
    assert "ESM3 API error (403): Model access denied" in capsys.readouterr().out
    plugin.pymol_cmd.load.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_http_endpoint_preserves_api_error(sdk, tmp_path, monkeypatch):
    sdk.client.return_value.generate.return_value = sdk.api.ESMProteinError(
        429, "Rate limit exceeded"
    )
    monkeypatch.chdir(tmp_path)
    server.pymol_cmd.load.reset_mock()
    with pytest.raises(HTTPException) as error:
        asyncio.run(server.run_esm3_prediction(server.Esm3Payload(sequence="ACDEFGHIK")))
    assert error.value.status_code == 500
    assert error.value.detail == "ESM3 API error (429): Rate limit exceeded"
    server.pymol_cmd.load.assert_not_called()
    assert list(tmp_path.iterdir()) == []
