import json
import os
import asyncio
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException
import logging
from .base import StructurePredictor

logger = logging.getLogger(__name__)


class Boltz2Predictor(StructurePredictor):
    """Structure predictor using Boltz2"""

    STATUS_URL = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/{task_id}"
    BOLTZ_URL = "https://health.api.nvidia.com/v1/biology/mit/boltz2/predict"
    MSA_URL = "https://health.api.nvidia.com/v1/biology/colabfold/msa-search/predict"

    def __init__(self, workdir: Optional[str] = None):
        """Initialize Boltz2 predictor

        Args:
            workdir: Directory to save prediction results
        """
        super().__init__(workdir)
        self.api_key = os.environ.get("NVCF_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Please set NVCF_API_KEY（export NVCF_API_KEY=...）before using Boltz2."
            )

    async def get_colab_msa(self, sequence: str) -> str:
        data = {
            "sequence": sequence,
            "e_value": 0.0001,
            "iterations": 1,
            "databases": ["Uniref30_2302"],
            "output_alignment_formats": ["a3m"],
        }

        print("Making MSA request...")
        result = await self._make_nvcf_call(function_url=self.MSA_URL, data=data)
        return result

    async def convert_to_boltz_json(self, gui_data):
        """
        Converts the final_data list from the Streamlit app into the Boltz JSON format.

        Args:
            final_data: A dictionary of entities and settings.

        Returns:
            dict: A dictionary formatted for Boltz API input.
        """
        import re

        boltz_json = {"polymers": [], "ligands": []}
        # --- Step 1: Process binding affinity settings first ---
        affinity_target_id = None

        # Find and remove the settings dictionary from the list
        # Using a list comprehension to create a new list without the settings
        entities = gui_data.get("entities", [])
        affinity_settings = gui_data.get("binding_affinity_settings", None)
        name = gui_data.get("name", None)
        diffusion_samples = gui_data.get("diffusion_samples", 1)

        if affinity_settings and affinity_settings.get("calculate_affinity"):
            # Parse the chain ID from a string like "Ligand (CCD) CHAIN_ID: B"
            selected_ligand_str = affinity_settings.get("selected_ligand", "")
            match = re.search(r"CHAIN_ID:\s*(\w+)", selected_ligand_str)
            if match:
                affinity_target_id = match.group(1)

        # --- Step 2: Iterate through entities and populate polymers and ligands ---
        for entity in entities:
            entity_type = entity.get("type")
            chain_id = entity.get("chain_id")

            # Handle Polymers
            if entity_type in ["Protein", "DNA", "RNA"]:
                sequence = entity.get("sequence", "")
                polymer = {
                    "id": chain_id,
                    "molecule_type": entity_type.lower(),
                    "sequence": sequence,
                    "cyclic": entity.get("cyclic", False),
                    "modifications": entity.get("modifications", []),
                }
                if entity_type == "Protein":
                    if entity.get("msa", False):
                        # Here we would normally generate or fetch an MSA.
                        # For simplicity, we'll create a dummy MSA entry.
                        # In a real application, you might integrate with an MSA generation tool.
                        msa_result = await self.get_colab_msa(sequence)
                        polymer["msa"] = msa_result["alignments"]
                    else:
                        # Create a placeholder MSA as required by the Boltz format
                        polymer["msa"] = {
                            "uniref90": {
                                "a3m": {
                                    "alignment": f">chain_{chain_id}\n{sequence}",
                                    "format": "a3m",
                                }
                            }
                        }
                boltz_json["polymers"].append(polymer)

            # Handle Ligands
            elif entity_type in ["Ligand (CCD)", "Ligand (SMILES)"]:
                # IMPORTANT: Boltz requires a SMILES string. This script assumes the input
                # ccd_string or smiles_string is a valid SMILES. It cannot convert names like "ATP".
                entity_string = entity.get("smiles_string") or entity.get(
                    "ccd_string", ""
                )
                lig_param = "smiles" if entity_type == "Ligand (SMILES)" else "ccd"
                ligand = {
                    lig_param: entity_string,
                    "id": chain_id,
                    # Set predict_affinity based on the settings processed earlier
                    "predict_affinity": (chain_id == affinity_target_id),
                }
                boltz_json["ligands"].append(ligand)
        if not boltz_json["ligands"]:
            del boltz_json["ligands"]  # Remove empty ligands list if no ligands present
        if not boltz_json["polymers"]:
            del boltz_json[
                "polymers"
            ]  # Remove empty polymers list if no polymers present
        return boltz_json, name, affinity_target_id, diffusion_samples

    async def predict(self, boltz_json: dict, **kwargs) -> Dict[str, Any]:
        """Predict protein structure using Boltz2

        Args:
            boltz_json: Input data in Boltz JSON format
            **kwargs: Additional parameters including:
                recycling_steps: Number of recycling steps (default: 1)
                sampling_steps: Number of sampling steps (default: 50)
                diffusion_samples: Number of diffusion samples (default: 3)
                step_scale: Step scale factor (default: 1.2)
                without_potentials: Whether to disable potentials (default: True)

        Returns:
            Dictionary containing:
            - structures: List of predicted structures
            - confidence_scores: Confidence scores for predictions
        """
        # Prepare request data
        data = {
            "recycling_steps": kwargs.get("recycling_steps", 3),
            "sampling_steps": kwargs.get("sampling_steps", 20),
            "diffusion_samples": kwargs.get("diffusion_samples", 1),
            "step_scale": kwargs.get("step_scale", 1.6),
            "without_potentials": kwargs.get("without_potentials", True),
        }
        boltz_json.update(data)

        # instead of asyncio.run, we make the predict function async and call await here
        result = await self._make_nvcf_call(
            function_url=self.BOLTZ_URL,
            data=boltz_json,
            poll_seconds=kwargs.get("poll_seconds", 300),
            timeout_seconds=kwargs.get("timeout_seconds", 400),
        )

        return result

    async def _make_nvcf_call(
        self,
        function_url: str,
        data: Dict[str, Any],
        poll_seconds: int = 300,
        timeout_seconds: int = 400,
    ) -> Dict[str, Any]:
        """Make call to NVIDIA Cloud Functions with polling

        Args:
            function_url: API endpoint URL
            data: Request payload
            poll_seconds: Maximum polling time
            timeout_seconds: Request timeout

        Returns:
            API response data

        Raises:
            HTTPException: If API call fails
        """
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "NVCF-POLL-SECONDS": str(poll_seconds),
                "Content-Type": "application/json",
            }

            logger.debug(
                "Headers: %s",
                {k: v for k, v in headers.items() if k != "Authorization"},
            )
            logger.debug("Making NVCF call to %s", function_url)
            logger.debug("Data: %s", data)

            response = await client.post(
                function_url, json=data, headers=headers, timeout=timeout_seconds
            )

            logger.debug(
                "NVCF response: %s, %s", response.status_code, response.headers
            )

            if response.status_code == 202:
                # Handle 202 Accepted - poll for results
                task_id = response.headers.get("nvcf-reqid")
                if not task_id:
                    raise HTTPException(
                        status_code=500, detail="Missing nvcf-reqid header"
                    )

                while True:
                    status_response = await client.get(
                        self.STATUS_URL.format(task_id=task_id),
                        headers=headers,
                        timeout=timeout_seconds,
                    )

                    if status_response.status_code == 200:
                        return status_response.json()
                    elif status_response.status_code in [400, 401, 404, 422, 500]:
                        raise HTTPException(
                            status_code=status_response.status_code,
                            detail=f"Error polling results: {status_response.text}",
                        )

            elif response.status_code == 200:
                return response.json()

            raise HTTPException(status_code=response.status_code, detail=response.text)
