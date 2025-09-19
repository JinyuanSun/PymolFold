"""Utility functions for structure prediction and analysis"""
import re
import json
from pathlib import Path
import subprocess
import sys
from typing import Union, Dict, Any
from pymol import cmd as pymol_cmd

def pip_install(pkg, index_url=None):
    cmd = [sys.executable, "-m", "pip", "install", pkg]
    if index_url:
        cmd.extend(["-i", index_url])
    print(f"[PfPlugin] Installing {pkg}...")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in process.stdout:
            print(line.strip())
        process.wait()
        if process.returncode == 0:
            print(f"[PfPlugin] {pkg} installed successfully.")
        else:
            print(f"[PfPlugin] Failed to install {pkg}")
    except Exception as e:
        print(f"[PfPlugin] Failed to install {pkg}: {e}")
        
def cal_plddt(pdb_string: str) -> float:
    """Calculate average pLDDT score from PDB B-factors
    
    Args:
        pdb_string: PDB format structure string
        
    Returns:
        Average pLDDT score (0-100 scale)
    """
    lines = pdb_string.split("\n")
    plddts = []
    
    for line in lines:
        if " CA " in line:
            try:
                plddt = float(line[60:66])
                plddts.append(plddt)
            except (ValueError, IndexError):
                continue
                
    if not plddts:
        return 0.0
        
    # Convert 0-1 scale to 0-100 if needed
    if max(plddts) <= 1.0:
        plddts = [plddt * 100 for plddt in plddts]
        
    return sum(plddts) / len(plddts)

def color_plddt(selection="all"):
    """
    AUTHOR
    Jinyuan Sun

    DESCRIPTION
    Colors Predicted Structures by pLDDT

    USAGE
    color_plddt sele

    PARAMETERS

    sele (string)
    The name of the selection/object to color by pLDDT. Default: all
    """
    # Alphafold color scheme for plddt
    pymol_cmd.set_color("high_lddt_c", [0, 0.325490196078431, 0.843137254901961])
    pymol_cmd.set_color("normal_lddt_c", [
                  0.341176470588235, 0.792156862745098, 0.976470588235294])
    pymol_cmd.set_color("medium_lddt_c", [1, 0.858823529411765, 0.070588235294118])
    pymol_cmd.set_color("low_lddt_c", [1, 0.494117647058824, 0.270588235294118])

    # test the scale of predicted_lddt (0~1 or 0~100 ) as b-factors
    pymol_cmd.select("test_b_scale", f"b>1 and ({selection})")
    b_scale = pymol_cmd.count_atoms("test_b_scale")

    if b_scale > 0:
        pymol_cmd.select("high_lddt", f"({selection}) and (b >90 or b =90)")
        pymol_cmd.select("normal_lddt",
                   f"({selection}) and ((b <90 and b >70) or (b =70))")
        pymol_cmd.select("medium_lddt",
                   f"({selection}) and ((b <70 and b >50) or (b=50))")
        pymol_cmd.select(
            "low_lddt", f"({selection}) and ((b <50 and b >0 ) or (b=0))")
    else:
        pymol_cmd.select("high_lddt", f"({selection}) and (b >.90 or b =.90)")
        pymol_cmd.select("normal_lddt",
                   f"({selection}) and ((b <.90 and b >.70) or (b =.70))")
        pymol_cmd.select("medium_lddt",
                   f"({selection}) and ((b <.70 and b >.50) or (b=.50))")
        pymol_cmd.select(
            "low_lddt", f"({selection}) and ((b <.50 and b >0 ) or (b=0))")

    pymol_cmd.delete("test_b_scale")

    # set color based on plddt values
    pymol_cmd.color("high_lddt_c", "high_lddt")
    pymol_cmd.color("normal_lddt_c", "normal_lddt")
    pymol_cmd.color("medium_lddt_c", "medium_lddt")
    pymol_cmd.color("low_lddt_c", "low_lddt")

    # set background color
    pymol_cmd.bg_color("white")
    
def clean_sequence(sequence: str) -> str:
    """Clean amino acid sequence string
    
    Args:
        sequence: Raw sequence string
        
    Returns:
        Cleaned sequence with only valid amino acid letters
    """
    # Replace "/" with ":" and convert to uppercase
    sequence = re.sub("[^A-Z:]", "", sequence.replace("/", ":").upper())
    # Clean up colons
    sequence = re.sub(":+", ":", sequence)
    sequence = re.sub("^[:]+", "", sequence)
    sequence = re.sub("[:]+$", "", sequence)
    return sequence
    
def safe_filename(name: str) -> str:
    """Convert string to safe filename
    
    Args:
        name: Original filename string
        
    Returns:
        Safe filename with invalid characters removed/replaced
    """
    name = name.strip()
    # Remove/replace invalid characters
    name = re.sub(r"[\/\\\0]", "_", name)
    # Collapse multiple spaces/underscores
    name = re.sub(r"\s+", "_", name)
    return name or "model"

def save_json_output(
    data: Dict[str, Any],
    output_file: Union[str, Path],
    indent: int = 4
) -> Path:
    """Save prediction results to JSON file
    
    Args:
        data: Prediction results dictionary
        output_file: Output JSON file path
        indent: JSON indentation level
        
    Returns:
        Path to saved file
    """
    output_path = Path(output_file)
    output_path.write_text(
        json.dumps(data, indent=indent),
        encoding='utf-8'
    )
    return output_path