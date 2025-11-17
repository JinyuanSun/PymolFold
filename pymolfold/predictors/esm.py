"""ESM-based structure predictors"""

import os
import requests
from typing import Dict, Any, Optional
from .base import StructurePredictor


class ESM3Predictor(StructurePredictor):
    """Structure predictor using ESM-3"""

    def __init__(self, workdir: Optional[str] = None):
        super().__init__(workdir)
        self._check_esm_token()

    def _check_esm_token(self):
        """Check and load ESM API token"""
        self.token = os.environ.get("ESM_API_TOKEN")
        token_file = os.path.join(os.path.dirname(__file__), "..", ".esm3_token")

        if not self.token and os.path.exists(token_file):
            with open(token_file) as f:
                self.token = f.read().strip()

        if not self.token:
            raise RuntimeError(
                "ESM_API_TOKEN is not set. Get your token from "
                "https://forge.evolutionaryscale.ai"
            )

    def predict(self, sequence: str, **kwargs) -> Dict[str, Any]:
        """Predict structure using ESM-3

        Args:
            sequence: Amino acid sequence
            **kwargs:
                temperature: Sampling temperature (default: 0.7)
                num_steps: Number of steps (default: 8)
                model_name: Model name (default: "esm3-medium-2024-08")

        Returns:
            Dictionary with prediction results
        """
        # try:
        from esm.sdk import client
        from esm.sdk.api import ESMProtein, GenerationConfig

        # except ImportError:
        #     raise ImportError("Please install esm: pip install esm")

        model_name = kwargs.get("model_name", "esm3-medium-2024-08")
        model = client(
            model=model_name, url="https://forge.evolutionaryscale.ai", token=self.token
        )

        config = GenerationConfig(
            track="structure",
            num_steps=kwargs.get("num_steps", 8),
            temperature=kwargs.get("temperature", 0.7),
        )

        prompt = ESMProtein(sequence=sequence)
        prediction = model.generate(prompt, config)
        chain = prediction.to_protein_chain()

        return {
            "structures": [
                {
                    "structure": chain.to_pdb_string(),
                    "source": kwargs.get("name", "esm3_prediction"),
                }
            ],
            "confidence_scores": [None],  # pLDDT available in B-factors
        }


class ESMFoldPredictor(StructurePredictor):
    """Structure predictor using ESMFold API"""

    API_URL = "https://api.esmatlas.com/foldSequence/v1/pdb/"

    def predict(self, sequence: str, **kwargs) -> Dict[str, Any]:
        """Predict structure using ESMFold

        Args:
            sequence: Amino acid sequence
            **kwargs: Additional parameters (not used)

        Returns:
            Dictionary with prediction results
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            self.API_URL, headers=headers, data=sequence, verify=False
        )

        if response.status_code == 500:
            raise RuntimeError("ESMFold API internal server error")

        return {
            "structures": [
                {
                    "structure": response.content.decode("utf-8"),
                    "source": kwargs.get("name", "esmfold_prediction"),
                }
            ],
            "confidence_scores": [None],  # pLDDT available in B-factors
        }


# class PyMolFoldPredictor(StructurePredictor):
#     """Structure predictor using PyMolFold server"""

#     def __init__(self, workdir: Optional[str] = None, base_url: str = "https://api.cloudmol.org/"):
#         super().__init__(workdir)
#         self.base_url = base_url.rstrip("/") + "/"

#     def predict(self, sequence: str, **kwargs) -> Dict[str, Any]:
#         """Predict structure using PyMolFold server

#         Args:
#             sequence: Amino acid sequence
#             **kwargs: Additional parameters (not used)

#         Returns:
#             Dictionary with prediction results
#         """
#         headers = {"Content-Type": "application/x-www-form-urlencoded"}
#         response = requests.post(
#             f"{self.base_url}protein/esmfold/",
#             headers=headers,
#             data=sequence
#         )

#         if response.status_code == 500:
#             raise RuntimeError("PyMolFold server internal error")

#         pdb_string = response.content.decode("utf-8")
#         if pdb_string.startswith("PARENT"):
#             pdb_string = pdb_string.replace("PARENT N/A\n", "")

#         return {
#             "structures": [{
#                 "structure": pdb_string.replace("\\n", "\n"),
#                 "source": kwargs.get("name", "pymolfold_prediction")
#             }],
#             "confidence_scores": [None]  # pLDDT available in B-factors
#         }
