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
from typing import Tuple

from pymolfold.predictors import ESM3Predictor

# Global settings
OBJECT_FILENAME_MAP = {}
ABS_PATH = os.path.abspath("./")
AM_HEGELAB_API = "https://alphamissense.hegelab.org/structure/"

_original_load = pymol_cmd.load


def load(
    filename,
    object="",
    state=0,
    format="",
    finish=1,
    discrete=-1,
    quiet=1,
    multiplex=None,
    zoom=-1,
    partial=0,
    mimic=1,
    object_props=None,
    atom_props=None,
    *,
    _self=pymol_cmd,
):
    """
    Wrapper for pymol.cmd.load to track loaded objects.
    """
    # Record existing objects before loading
    try:
        pre_objects = set(_self.get_names("objects"))
    except Exception:
        pre_objects = set()

    # Call the original load function
    result = _original_load(
        filename,
        object,
        state,
        format,
        finish,
        discrete,
        quiet,
        multiplex,
        zoom,
        partial,
        mimic,
        object_props,
        atom_props,
        _self=_self,
    )
    try:
        post_objects = set(_self.get_names("objects"))
        new_objects = list(post_objects - pre_objects)

        # use provided object name if any
        obj_name = (object or "").strip()

        if obj_name:
            OBJECT_FILENAME_MAP[obj_name] = filename
        else:
            if len(new_objects) == 1:
                # only one new object detected
                OBJECT_FILENAME_MAP[new_objects[0]] = filename
            elif len(new_objects) > 1:
                # multiplex mode, multiple new objects detected
                for obj in new_objects:
                    OBJECT_FILENAME_MAP[obj] = filename
            else:
                # no new object detected
                # try to guess from filename
                import os

                base = os.path.basename(filename)
                guess = base.rsplit(".", 1)[0] if "." in base else base
                # only record if the object actually exists to avoid false positives
                if guess in post_objects:
                    OBJECT_FILENAME_MAP[guess] = filename
                else:
                    # if unable to guess, do not record; can print a warning if needed (controlled by quiet)
                    if not int(quiet):
                        print(
                            f'load(map): could not determine object name for "{filename}"'
                        )
    except Exception as e:
        if not int(quiet):
            print("load(map): failed to record mapping:", e)
    return result


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


def set_api_key(key_name, key_value):
    """
    Set API key in environment and .env file.
    Usage: set_apikey ESM_API_TOKEN your_token_value
    """
    import os
    from dotenv import set_key, find_dotenv

    os.environ[key_name] = key_value
    env_path = find_dotenv()
    if env_path:
        set_key(env_path, key_name, key_value)
    else:
        # If .env doesn't exist, create one
        with open(".env", "a") as f:
            f.write(f"{key_name}={key_value}\n")
    print(f"Set {key_name} in environment and .env file.")


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
        streamlit_path = shutil.which("streamlit")
        # Assuming your streamlit app is in a 'gui' subdirectory
        ui_path = os.path.join(os.path.dirname(__file__), "gui", "app.py")

        if not os.path.exists(ui_path):
            print(f"Streamlit UI file not found at: {ui_path}")
            return

        def is_port_in_use(port=8510):
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", port)) == 0

        if not is_port_in_use(8510):
            subprocess.Popen([streamlit_path, "run", ui_path])
        else:
            print("Streamlit is already running.")

        # webbrowser.open('http://localhost:8510')
    except Exception as e:
        print(f"Could not launch Streamlit UI: {e}")


def query_esm3(
    sequence: str,
    name: str = None,
    temperature: float = 0.7,
    num_steps: int = 8,
    model_name: str = "esm3-medium-2024-08",
):
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
            model_name=model_name,
        )

        saved_files = predictor.save_structures(result, name)
        if saved_files:
            first_file = saved_files[0]
            pymol_cmd.load(str(first_file))

            try:
                pdb_string = first_file.read_text()
                plddt = utils.cal_plddt(pdb_string)
                print(f"Structure saved in {first_file}.")
                print("=" * 40)
                print(f"    pLDDT: {plddt:.2f}")
                print("=" * 40)
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
            with open(output_filename, "wb") as file:
                file.write(data_content)
    pymol_cmd.load(output_filename)
    return 0


def fetch_af(uniprot_id):
    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
    pymol_cmd.do(f"load {url}")
    pymol_cmd.do(f"color_plddt AF-{uniprot_id}-F1-model_v4")


def _infer_object_name_from_path(path: str) -> str:
    base = os.path.basename(path)
    name = base.rsplit(".", 1)[0] if "." in base else base
    return name


def _resolve_obj_and_cif(arg: str, *, param_name: str) -> Tuple[str, str]:
    """
    Resolve an argument to (object_name, abs_cif_path).

    Accepts either:
      - PyMOL object name (must exist; CIF path taken from OBJECT_FILENAME_MAP)
      - Absolute path to .cif/.mmcif (loads into PyMOL and returns created object)

    Returns
    -------
    (obj_name, abs_path)
    """
    if not isinstance(arg, str) or not arg.strip():
        raise ValueError(
            f'"{param_name}" must be a non-empty string (object name or absolute CIF path).'
        )

    s = arg.strip()

    # Absolute path case
    if os.path.isabs(s):
        if not os.path.exists(s):
            raise FileNotFoundError(f'"{param_name}" path does not exist: {s}')
        if not (s.lower().endswith(".cif") or s.lower().endswith(".mmcif")):
            raise ValueError(
                f'"{param_name}" must point to a .cif/.mmcif file, got: {s}'
            )

        pre = set(pymol_cmd.get_names("objects"))
        # Let PyMOL decide object name; we detect it post-load
        try:
            pymol_cmd.load(s, quiet=1)
        except Exception as e:
            print(f'Warning: failed to load "{s}" into PyMOL: {e}')
        post = set(pymol_cmd.get_names("objects"))
        new_objs = list(post - pre)

        if len(new_objs) == 1:
            obj_name = new_objs[0]
        else:
            # Fallback to filename prefix if we can't uniquely detect
            obj_name = _infer_object_name_from_path(s)
            if obj_name not in post:
                # If prefix is taken and PyMOL auto-suffixed, best-effort pick any matching prefix
                candidates = [n for n in post if n.startswith(obj_name)]
                if candidates:
                    obj_name = sorted(candidates)[0]  # deterministic pick

        # Map it so later calls can resolve by object name too
        OBJECT_FILENAME_MAP[obj_name] = os.path.abspath(s)
        return obj_name, os.path.abspath(s)

    # Object name case
    obj = s
    if obj not in pymol_cmd.get_names("objects"):
        # The object should exist for alignment; still allow using the path if we have one
        print(
            f'Warning: object "{obj}" not found in current session. If PXMeter runs, alignment will be skipped for this object.'
        )

    path = OBJECT_FILENAME_MAP.get(obj)
    if not path:
        raise KeyError(
            f'Object "{obj}" not found in OBJECT_FILENAME_MAP. '
            f"Load it via the wrapped cmd.load so the map gets populated, or pass an absolute CIF path."
        )
    if not os.path.isabs(path) or not os.path.exists(path):
        raise FileNotFoundError(
            f'OBJECT_FILENAME_MAP has an invalid path for "{obj}": {path!r}'
        )
    if not (path.lower().endswith(".cif") or path.lower().endswith(".mmcif")):
        raise ValueError(
            f'OBJECT_FILENAME_MAP entry for "{obj}" is not a CIF file: {path!r}'
        )
    return obj, os.path.abspath(path)


def pxmeter_align(ref_cif: str, model_cif: str, verbose: bool = True) -> dict:
    """
    Evaluate with PXMeter using either object names or absolute CIF paths.
    Additionally, CEAlign (model -> ref) and zoom before running PXMeter.

    Parameters
    ----------
    ref_cif : str
        PyMOL object name or absolute .cif/.mmcif path. Paths are loaded.
    model_cif : str
        PyMOL object name or absolute .cif/.mmcif path. Paths are loaded.
    verbose : bool
        Whether to print progress messages.

    Returns
    -------
    dict
        PXMeter result (json-like dict)
    """
    from shadowpxmeter.eval import evaluate

    # import utils  # must provide visualize_pxmeter_metrics

    try:
        ABS_PATH  # expected to be defined elsewhere
    except NameError:
        ABS_PATH = os.getcwd()

    # Resolve to (object_name, absolute_path)
    ref_obj, ref_path = _resolve_obj_and_cif(ref_cif, param_name="ref_cif")
    model_obj, model_path = _resolve_obj_and_cif(model_cif, param_name="model_cif")

    # CEAlign model -> ref, then zoom on both
    ceinfo = None
    try:
        if ref_obj in pymol_cmd.get_names(
            "objects"
        ) and model_obj in pymol_cmd.get_names("objects"):
            if verbose:
                print(f'Aligning "{model_obj}" to "{ref_obj}" with CEAlign...')
            ceinfo = pymol_cmd.cealign(ref_obj, model_obj)  # target, mobile
            # Zoom to both objects (no animation to be quick and script-friendly)
            pymol_cmd.zoom(f"({ref_obj}) or ({model_obj})", animate=-1)
            if verbose and isinstance(ceinfo, dict):
                rmsd = ceinfo.get("RMSD")
                naln = ceinfo.get("Naligned")
                print(f"CEAlign done. RMSD={rmsd}, Naligned={naln}")
        else:
            if verbose:
                print(
                    "Skip alignment: one or both objects are not present in the current session."
                )
    except Exception as e:
        print(f"Warning: CEAlign failed: {e}")

    if verbose:
        print("Evaluating structure with PXMeter...")
    metric_result = evaluate(
        ref_cif=ref_path,
        model_cif=model_path,
    )

    json_dict = metric_result.to_json_dict()

    out_dir = os.path.join(ABS_PATH, "pxmeter_results")
    os.makedirs(out_dir, exist_ok=True)
    # If you have a visualization util, uncomment:
    utils.visualize_pxmeter_metrics(json_dict, output_dir=out_dir)

    if verbose:
        import json

        print("PXMeter results:\n", json.dumps(json_dict, indent=2))
        print(f"PXMeter results written to: {out_dir}")

    return json_dict


# def pxmeter_align(ref_cif, model_cif):
#     """
#     https://github.com/bytedance/PXMeter
#     Only support PPI and CIF format
#     Must enter path to cif files, no existed way to get object path in PyMOL
#     """
#     from shadowpxmeter.eval import evaluate

#     print("Evaluating structure with PXMeter...")
#     metric_result = evaluate(
#         ref_cif=ref_cif,
#         model_cif=model_cif,
#     )

#     json_dict = metric_result.to_json_dict()
#     utils.visualize_pxmeter_metrics(
#         json_dict, output_dir=os.path.join(ABS_PATH, "pxmeter_results")
#     )
#     # return json_dict


# Register commands
def __init_plugin__(app=None):
    """Initialize the plugin when PyMOL loads it

    This function is called by PyMOL when the plugin is loaded.
    """
    import dotenv

    dotenv.load_dotenv(dotenv.find_dotenv())

    pymol_cmd.extend("boltz2", init_boltz2_gui)
    pymol_cmd.extend("esm3", query_esm3)
    pymol_cmd.extend("set_workdir", set_workdir)
    pymol_cmd.extend("set_base_url", set_base_url)
    pymol_cmd.extend("set_api_key", set_api_key)

    pymol_cmd.extend("color_plddt", utils.color_plddt)
    pymol_cmd.extend("pxmeter_align", pxmeter_align)
    pymol_cmd.extend("fetch_am", query_am_hegelab)
    pymol_cmd.extend("fetch_af", fetch_af)
    pymol_cmd.extend("load", load)
    pymol_cmd.load = load  # Override the original load command

    pymol_cmd.auto_arg[0]["pxmeter_align"] = [pymol_cmd.object_sc, "object", ""]
    pymol_cmd.auto_arg[1]["pxmeter_align"] = [pymol_cmd.object_sc, "object", ""]

    print(f"PymolFold v{__version__} loaded successfully!")
    return True
