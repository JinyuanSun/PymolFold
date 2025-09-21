"""PyMOL plugin for structure prediction"""
import os
import threading
import time
import requests
from pymol import cmd as pymol_cmd
from .version import __version__
from . import utils
from . import server
import subprocess
import shutil

from pymolfold.predictors import (ESM3Predictor)

# Global settings
ABS_PATH = os.path.abspath("./")
AM_HEGELAB_API = 'https://alphamissense.hegelab.org/structure/'

def set_workdir(path):
    """Set working directory for output files"""
    global ABS_PATH
    ABS_PATH = path
    if ABS_PATH[0] == "~":
        ABS_PATH = os.path.join(os.path.expanduser("~"), ABS_PATH[2:])
    print(f"Results will be saved to {ABS_PATH}")

def set_base_url(url):
    """Set base URL for PyMolFold server"""
    global BASE_URL
    BASE_URL = url
    
########## Server ##########
def init_boltz2_gui():
    """Main function called by PyMOL to initialize the plugin."""
    # Run the FastAPI server in a separate thread.
    # This is CRUCIAL because it doesn't block PyMOL's main thread.
    server_thread = threading.Thread(target=server.run_server)
    server_thread.daemon = True
    server_thread.start()
    # Give the server a moment to start
    time.sleep(2)

    # Launch the Streamlit UI
    try:
        streamlit_path = shutil.which('streamlit')
        # Assuming your streamlit app is in a 'gui' subdirectory
        ui_path = os.path.join(os.path.dirname(__file__), 'gui', 'app.py')
        
        if not os.path.exists(ui_path):
            print(f"Streamlit UI file not found at: {ui_path}")
            return

        def is_port_in_use(port=8510):
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0

        if not is_port_in_use(8510):
            subprocess.Popen([streamlit_path, 'run', ui_path])
        else:
            print("Streamlit is already running.")

        # webbrowser.open('http://localhost:8510')
    except Exception as e:
       print(f"Could not launch Streamlit UI: {e}")
####### Server End #########
    
# def query_boltz2(gui_data, load_in_pymol: bool = True, **kwargs):
#     """Predict protein structure using Boltz2
    
#     Args:
#         sequence: Amino acid sequence
#         name: Name for output files (default: derived from sequence)
#         **kwargs: Additional Boltz2 parameters
#     """
   
        
#     predictor = Boltz2Predictor(workdir=ABS_PATH)
#     boltz_json, name = predictor.convert_to_boltz_json(gui_data)
#     try:
#         result = predictor.predict(boltz_json, **kwargs)
#         saved_files = predictor.save_structures(result, name)

#         if not saved_files:
#             print("No structures were generated")
#             return []

#         # If caller asked for PyMOL loading (default), load the first file and
#         # print pLDDT score as before. Otherwise just return the list of saved
#         # files so the server can load them into PyMOL.
#         if load_in_pymol:
#             for file in saved_files:
#                 pymol_cmd.load(str(file))

#                 try:
#                     pdb_string = file.read_text()
#                     plddt = utils.cal_plddt(pdb_string)
#                     print("="*40)
#                     print(f"    pLDDT: {plddt:.2f}")
#                     print("="*40)
#                 except Exception:
#                     print("Could not calculate pLDDT score")

#         return saved_files

#     except Exception as e:
#         print(f"Error during prediction: {str(e)}")
#         return []

def query_esm3(sequence: str, name: str = None, temperature: float = 0.7,
               num_steps: int = 8, model_name: str = "esm3-medium-2024-08"):
    """Predict protein structure using ESM-3
    
    Args:
        sequence: Amino acid sequence
        name: Name for output files
        temperature: Sampling temperature
        num_steps: Number of prediction steps
        model_name: Model name/version
    """
    sequence = utils.clean_sequence(sequence)
    if not name:
        name = sequence[:3] + sequence[-3:]
        
    predictor = ESM3Predictor(workdir=ABS_PATH)
    try:
        result = predictor.predict(
            sequence,
            name=name,
            temperature=temperature,
            num_steps=num_steps,
            model_name=model_name
        )
        
        saved_files = predictor.save_structures(result, name)
        if saved_files:
            first_file = saved_files[0]
            pymol_cmd.load(str(first_file))
            
            try:
                pdb_string = first_file.read_text()
                plddt = utils.cal_plddt(pdb_string)
                print("="*40)
                print(f"    pLDDT: {plddt:.2f}")
                print("="*40)
            except:
                print("Could not calculate pLDDT score")
        else:
            print("No structures were generated")
            
    except Exception as e:
        print(f"Error during prediction: {str(e)}")

def query_am_hegelab(name):
    try:
        url = AM_HEGELAB_API + name
        response = requests.get(url)
        response.raise_for_status()  # This will raise a HTTPError for bad responses (4xx and 5xx)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    else:
        # Follow the redirect and get the actual data URL
        data_url = response.url
        
        try:
            data_response = requests.get(data_url)
            data_response.raise_for_status()  # This will raise a HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        else:
            data_content = data_response.content
            
            # Save the data to a file
            output_filename = os.path.join(ABS_PATH, name) + ".pdb"
            with open(output_filename, 'wb') as file:
                file.write(data_content)
    pymol_cmd.load(output_filename)
    return 0

def fetch_af(uniprot_id):
    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
    pymol_cmd.do(f"load {url}")
    pymol_cmd.do(f"color_plddt AF-{uniprot_id}-F1-model_v4")


# Register commands
def __init_plugin__(app=None):
    """Initialize the plugin when PyMOL loads it
    
    This function is called by PyMOL when the plugin is loaded.
    """
    pymol_cmd.extend("boltz2", init_boltz2_gui)
    pymol_cmd.extend("esm3", query_esm3)
    # pymol_cmd.extend("esmfold", query_esmfold)
    # pymol_cmd.extend("pymolfold", query_pymolfold)
    pymol_cmd.extend("set_workdir", set_workdir)
    pymol_cmd.extend("set_base_url", set_base_url)

    pymol_cmd.extend("color_plddt", utils.color_plddt)
    # pymol_cmd.auto_arg[0]["color_plddt"] = [cmd.object_sc, "object", ""]
    pymol_cmd.extend("fetch_am", query_am_hegelab)
    pymol_cmd.extend("fetch_af", fetch_af)
    # Register local HTTP handler so the web UI can call back into query_boltz2
    # try:
    #     server.register_handler(query_boltz2)
    #     server.start_server()
    # except Exception:
    #     # If Flask not installed or server fails to start, keep going silently
    #     pass

    print(f"PymolFold v{__version__} loaded successfully!")
    return True