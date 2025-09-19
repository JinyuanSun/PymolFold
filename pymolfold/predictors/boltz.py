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
    PUBLIC_URL = "https://health.api.nvidia.com/v1/biology/mit/boltz2/predict"
    
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
            
    def predict(self, sequence: str, **kwargs) -> Dict[str, Any]:
        """Predict protein structure using Boltz2
        
        Args:
            sequence: Amino acid sequence
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
            "polymers": [{
                "id": "A",
                "molecule_type": "protein",
                "sequence": sequence,
                "msa": {
                    "uniref90": {
                        "a3m": {
                            "alignment": f">seq1\n{sequence}",
                            "format": "a3m"
                        }
                    }
                }
            }],
            # "ligands": [{
            #     "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
            #     "id": "L1",
            #     "predict_affinity": True
            # }],
            "recycling_steps": kwargs.get('recycling_steps', 1),
            "sampling_steps": kwargs.get('sampling_steps', 50),
            "diffusion_samples": kwargs.get('diffusion_samples', 3),
            "step_scale": kwargs.get('step_scale', 1.2),
            "without_potentials": kwargs.get('without_potentials', True)
        }
        
        # Make async call in sync context
        result = asyncio.run(self._make_nvcf_call(
            function_url=self.PUBLIC_URL,
            data=data,
            poll_seconds=kwargs.get('poll_seconds', 300),
            timeout_seconds=kwargs.get('timeout_seconds', 400)
        ))
        
        return result
        
    async def _make_nvcf_call(
        self,
        function_url: str,
        data: Dict[str, Any],
        poll_seconds: int = 300,
        timeout_seconds: int = 400
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
                "Content-Type": "application/json"
            }
            
            logger.debug("Headers: %s", 
                {k:v for k,v in headers.items() if k != "Authorization"})
            logger.debug("Making NVCF call to %s", function_url)
            logger.debug("Data: %s", data)
            
            response = await client.post(
                function_url,
                json=data,
                headers=headers,
                timeout=timeout_seconds
            )
            
            logger.debug("NVCF response: %s, %s", 
                response.status_code, response.headers)
                
            if response.status_code == 202:
                # Handle 202 Accepted - poll for results
                task_id = response.headers.get("nvcf-reqid")
                if not task_id:
                    raise HTTPException(
                        status_code=500,
                        detail="Missing nvcf-reqid header"
                    )
                    
                while True:
                    status_response = await client.get(
                        self.STATUS_URL.format(task_id=task_id),
                        headers=headers,
                        timeout=timeout_seconds
                    )
                    
                    if status_response.status_code == 200:
                        return status_response.json()
                    elif status_response.status_code in [400, 401, 404, 422, 500]:
                        raise HTTPException(
                            status_code=status_response.status_code,
                            detail=f"Error polling results: {status_response.text}"
                        )
                        
            elif response.status_code == 200:
                return response.json()
                
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )