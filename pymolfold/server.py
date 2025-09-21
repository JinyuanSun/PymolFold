"""Lightweight local HTTP server to accept plugin requests from the Streamlit UI.

This module intentionally avoids importing Flask at import time so the package
doesn't hard-require Flask for users who don't use the web UI. If Flask is
available it will provide a /run_boltz2 endpoint that forwards parameters to a
registered handler (the plugin's query_boltz2 function).
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .predictors import Boltz2Predictor
from pymol import cmd as pymol_cmd

class Payload(BaseModel):
    sub_data: Dict[str, Any]

# --- FastAPI Server Application ---
app = FastAPI()
server_instance = None

@app.post("/run_boltz2")
async def run_boltz2_prediction(payload: Payload):
    """Endpoint to receive data from Streamlit, run prediction, and load into PyMOL."""
    try:
        predictor = Boltz2Predictor()
        boltz_json, name = predictor.convert_to_boltz_json(payload.sub_data)
        
        result = await predictor.predict(boltz_json) # Assuming predict is now async
        saved_files = predictor.save_structures(result, name)

        if not saved_files:
            return {"status": "warning", "message": "No structures were generated."}

        # Load into PyMOL from the main thread
        for file_path in saved_files:
            pymol_cmd.load(str(file_path))
        
        return {"status": "success", "message": f"Loaded {len(saved_files)} files into PyMOL."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shutdown")
async def shutdown_server():
    """Endpoint to shut down the server."""
    global server_instance
    if server_instance:
        server_instance.should_exit = True
        return {"status": "shutdown initiated"}
    return {"status": "error", "message": "Server instance not found."}

def run_server():
    """Function to run the FastAPI server."""
    global server_instance
    config = uvicorn.Config(app, host="127.0.0.1", port=5002, log_level="info")
    server_instance = uvicorn.Server(config)
    server_instance.run()

