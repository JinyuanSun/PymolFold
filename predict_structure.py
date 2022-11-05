from pymol import cmd
import requests
import re
import os

ABS_PATH = os.path.abspath("./")


def cal_plddt(pdb_string: str):
    """read b-factors of ca

    Args:
        pdb_string (str): _description_
    """

    lines = pdb_string.split("\n")
    plddts = []
    for line in lines:
        if " CA " in line:
            plddt = float(line[60:66])
            plddts.append(plddt)
    if max(plddts) <= 1.0:
        plddts =[ plddt * 100 for plddt in plddts]
        print("Guessing the scale is [0,1], we scale it to [0, 100]")
    else:
        print("Guessing the scale is [0,100]")
    return sum(plddts) / len(plddts)


def query_esmfold(sequence: str, name: str = None):
    """Predict protein structure with ESMFold

    Args:
        sequence (str): amino acid sequence
        name (str, optional): _description_. Defaults to None.
    """
    sequence = re.sub("[^A-Z:]", "", sequence.replace("/", ":").upper())
    sequence = re.sub(":+", ":", sequence)
    sequence = re.sub("^[:]+", "", sequence)
    sequence = re.sub("[:]+$", "", sequence)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        "https://api.esmatlas.com/foldSequence/v1/pdb/", headers=headers, data=sequence
    )
    if not name:
        name = sequence[:3] + sequence[-3:]
    pdb_filename = os.path.join(ABS_PATH, name) + ".pdb"
    pdb_string = response.content.decode("utf-8")
    if pdb_string.startswith("HEADER"):
        with open(pdb_filename, "w") as out:
            out.write(pdb_string)
        print(f"Results saved to {pdb_filename}")
        plddt = cal_plddt(pdb_string)
        print("="*40)
        print("    pLDDT: "+"{:.2f}".format(plddt))
        print("="*40)
        cmd.load(pdb_filename)
    else:
        print(pdb_string)


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
    cmd.set_color("high_lddt_c", [0, 0.325490196078431, 0.843137254901961])
    cmd.set_color("normal_lddt_c", [0.341176470588235, 0.792156862745098, 0.976470588235294])
    cmd.set_color("medium_lddt_c", [1, 0.858823529411765, 0.070588235294118])
    cmd.set_color("low_lddt_c", [1, 0.494117647058824, 0.270588235294118])

    # test the scale of predicted_lddt (0~1 or 0~100 ) as b-factors
    cmd.select("test_b_scale", f"b>1 and ({selection})")
    b_scale = cmd.count_atoms("test_b_scale")

    if b_scale > 0:
        cmd.select("high_lddt", f"({selection}) and (b >90 or b =90)")
        cmd.select("normal_lddt", f"({selection}) and ((b <90 and b >70) or (b =70))")
        cmd.select("medium_lddt", f"({selection}) and ((b <70 and b >50) or (b=50))")
        cmd.select("low_lddt", f"({selection}) and ((b <50 and b >0 ) or (b=0))")
    else:
        cmd.select("high_lddt", f"({selection}) and (b >.90 or b =.90)")
        cmd.select("normal_lddt", f"({selection}) and ((b <.90 and b >.70) or (b =.70))")
        cmd.select("medium_lddt", f"({selection}) and ((b <.70 and b >.50) or (b=.50))")
        cmd.select("low_lddt", f"({selection}) and ((b <.50 and b >0 ) or (b=0))")

    cmd.delete("test_b_scale")

    # set color based on plddt values
    cmd.set("cartoon_color", "high_lddt_c", "high_lddt")
    cmd.set("cartoon_color", "normal_lddt_c", "normal_lddt")
    cmd.set("cartoon_color", "medium_lddt_c", "medium_lddt")
    cmd.set("cartoon_color", "low_lddt_c", "low_lddt")

    # set background color
    cmd.bg_color("white")


cmd.extend("color_plddt", color_plddt)
cmd.auto_arg[0]["color_plddt"] = [cmd.object_sc, "object", ""]
cmd.extend("esmfold", query_esmfold)
