"""PyMOL plugin for structure prediction"""
import os
import requests
from pymol import cmd as pymol_cmd

from .version import __version__
from . import utils

# # Add package root to Python path
# PACKAGE_ROOT = Path(__file__).parent.parent
# if str(PACKAGE_ROOT) not in sys.path:
#     sys.path.insert(0, str(PACKAGE_ROOT))

# 修改预测器导入
from pymolfold.predictors import (
    Boltz2Predictor,
    ESM3Predictor,
    # ESMFoldPredictor,
    # PyMolFoldPredictor
)
# from pymolfold import utils

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

def query_boltz2(sequence: str, name: str = None, **kwargs):
    """Predict protein structure using Boltz2
    
    Args:
        sequence: Amino acid sequence
        name: Name for output files (default: derived from sequence)
        **kwargs: Additional Boltz2 parameters
    """
    sequence = utils.clean_sequence(sequence)
    if not name:
        name = sequence[:3] + sequence[-3:]
        
    predictor = Boltz2Predictor(workdir=ABS_PATH)
    try:
        result = predictor.predict(sequence, **kwargs)
        
        # Save and load first structure
        saved_files = predictor.save_structures(result)
        if saved_files:
            first_file = saved_files[0]
            pymol_cmd.load(str(first_file))
            
            # Show pLDDT score
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
        
        saved_files = predictor.save_structures(result)
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

def query_esmfold(sequence: str, name: str = None):
    """Predict protein structure using ESMFold API
    
    Args:
        sequence: Amino acid sequence
        name: Name for output files
    """
    sequence = utils.clean_sequence(sequence)
    if not name:
        name = sequence[:3] + sequence[-3:]
        
    predictor = ESMFoldPredictor(workdir=ABS_PATH)
    try:
        result = predictor.predict(sequence, name=name)
        
        saved_files = predictor.save_structures(result)
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
        if isinstance(e, RuntimeError) and "internal server error" in str(e):
            print("ESMFold API error, trying PyMolFold server instead...")
            query_pymolfold(sequence, name)
        else:
            print(f"Error during prediction: {str(e)}")

def query_pymolfold(sequence: str, name: str = None):
    """Predict protein structure using PyMolFold server
    
    Args:
        sequence: Amino acid sequence
        name: Name for output files
    """
    sequence = utils.clean_sequence(sequence)
    if not name:
        name = sequence[:3] + sequence[-3:]
        
    predictor = PyMolFoldPredictor(workdir=ABS_PATH)
    try:
        result = predictor.predict(sequence, name=name)
        
        saved_files = predictor.save_structures(result)
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
    pymol_cmd.extend("boltz2", query_boltz2)
    pymol_cmd.extend("esm3", query_esm3)
    # pymol_cmd.extend("esmfold", query_esmfold)
    # pymol_cmd.extend("pymolfold", query_pymolfold)
    pymol_cmd.extend("set_workdir", set_workdir)
    pymol_cmd.extend("set_base_url", set_base_url)

    pymol_cmd.extend("color_plddt", utils.color_plddt)
    # pymol_cmd.auto_arg[0]["color_plddt"] = [cmd.object_sc, "object", ""]
    pymol_cmd.extend("fetch_am", query_am_hegelab)
    pymol_cmd.extend("fetch_af", fetch_af)
    print(f"PymolFold v{__version__} loaded successfully!")
    return True