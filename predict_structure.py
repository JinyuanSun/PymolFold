from __future__ import print_function

from pymol import cmd
import requests
import re
import os

ABS_PATH = os.path.abspath('./')

def query_esmfold(sequence, name=None):
    """Predict protein structure with ESMFold

    Args:
        sequence (str): amino acid sequence
        name (str, optional): _description_. Defaults to None.
    """
    sequence = re.sub("[^A-Z:]", "", sequence.replace("/",":").upper())
    sequence = re.sub(":+",":",sequence)
    sequence = re.sub("^[:]+","",sequence)
    sequence = re.sub("[:]+$","",sequence)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }


    response = requests.post('https://api.esmatlas.com/foldSequence/v1/pdb/', headers=headers, data=sequence)
    if not name:
        name = sequence[:3] + sequence[-3:] 
    pdb_filename = os.path.join(ABS_PATH, name) + ".pdb"
    pdb_string = response.content.decode('utf-8')
    if pdb_string.startswith("HEADER"):
        with open(pdb_filename, "w") as out:
            out.write(pdb_string)
        print("Results saved to %s" %pdb_filename)
    else:
        print(pdb_string)
    cmd.load(pdb_filename)

def coloresm(selection="all"):
    
    """
    AUTHOR
    Jinyuan Sun

    DESCRIPTION
    Colors ESMFold structures by pLDDT

    USAGE
    coloresm sele

    PARAMETERS

    sele (string)
    The name of the selection/object to color by pLDDT. Default: all
    """
    cmd.set_color("high_lddt_c", [0,0.325490196078431,0.843137254901961 ])
    cmd.set_color("normal_lddt_c", [0.341176470588235,0.792156862745098,0.976470588235294])
    cmd.set_color("medium_lddt_c", [1,0.858823529411765,0.070588235294118])
    cmd.set_color("low_lddt_c", [1,0.494117647058824,0.270588235294118])
    cmd.color("high_lddt_c", "(%s) and b > 0.89" %selection)
    cmd.color("normal_lddt_c", "(%s) and b < 0.9 and b > 0.69" %selection)
    cmd.color("medium_lddt_c", "(%s) and b < 0.70 and b > 0.49" %selection)
    cmd.color("low_lddt_c", "(%s) and b < 0.50" %selection)

query_esmfold.__annotations__ = {'sequence': str}

cmd.extend("coloresm", coloresm)
cmd.auto_arg[0]["coloresm"] = [cmd.object_sc, "object", ""]
cmd.extend("esmfold", query_esmfold)

