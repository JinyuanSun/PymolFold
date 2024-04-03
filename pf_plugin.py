from pymol import cmd
import requests
import re
import os
import json

# BASE_URL = "http://region-8.seetacloud.com:42711/"
BASE_URL = "https://api.cloudmol.org/"
ESMFOLD_API = "https://api.esmatlas.com/foldSequence/v1/pdb/"
AM_HEGELAB_API = 'https://alphamissense.hegelab.org/structure/'
ABS_PATH = os.path.abspath("./")

def set_workdir(path):
    global ABS_PATH
    ABS_PATH = path
    if ABS_PATH[0] == "~":
        ABS_PATH = os.path.join(os.path.expanduser("~"), ABS_PATH[2:])
    print(f"Results will be saved to {ABS_PATH}")

def set_base_url(url):
    global BASE_URL
    BASE_URL = url

def ls_fix(selection, HOH="N"):
    sel = selection
    objs = cmd.get_object_list(sel)
    list_sele = []
    sel = selection+" and not resn HOH"

    for a in range(len(objs)):
        m1 = cmd.get_model(sel+" and "+objs[a])
    for x in range(len(m1.atom)):
        if m1.atom[x-1].resi != m1.atom[x].resi:
            list_sele.append(m1.atom[x].resi)
    print(",".join(list_sele))
    return ",".join(list_sele)


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
        plddts = [plddt * 100 for plddt in plddts]
        print("Guessing the scale is [0,1], we scale it to [0, 100]")
    else:
        print("Guessing the scale is [0,100]")
    return sum(plddts) / len(plddts)


def query_pymolfold(sequence: str, name: str = None, num_recycle: int = 0):
    if num_recycle != 0:
        print("The `num_recycle` was deprecated.")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(f"{BASE_URL}protein/esmfold/", headers=headers, data=sequence)
    
    if response.status_code == 500:  # HTTP status for Internal Server Error
        print("PymolFold API resulted in an INTERNAL SERVER ERROR. Switching to ESMFold...")
        query_esmfold(sequence, name)
        return 0
    if not name:
        name = sequence[:3] + sequence[-3:]
    pdb_string = response.content.decode("utf-8")
    pdb_filename = os.path.join(ABS_PATH, name) + ".pdb"
    if pdb_string.startswith("PARENT"):
        pdb_string = pdb_string.replace("PARENT N/A\n", "")
        with open(pdb_filename, "w") as out:
            out.write(pdb_string.replace('\\n', '\n'))
        print(f"Results saved to {pdb_filename}")
        plddt = cal_plddt(pdb_string)
        print("="*40)
        print("    pLDDT: "+"{:.2f}".format(plddt))
        print("="*40)
        cmd.load(pdb_filename)
    else:
        print(pdb_string)
    return 0

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
    cmd.load(output_filename)
    return 0


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

    response = requests.post(ESMFOLD_API, headers=headers, data=sequence, verify=False)
    if response.status_code == 500:  # HTTP status for Internal Server Error
        print("ESMFold API resulted in an INTERNAL SERVER ERROR. Switching to PyMolFold...")
        query_pymolfold(sequence, name)
        return 0
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
    return 0


def query_mpnn(path_to_pdb: str, fix_pos=None, chain=None, rm_aa=None, inverse=False, homooligomeric=False):
    """query ProteinMPNN server for de novo protein design

    Args:
        path_to_pdb (str): _description_

    Returns:
        _type_: _description_
    """
    headers = {
        'accept': 'application/json',
    }
    files = {
        'file': open(path_to_pdb, 'rb'),
    }

    if fix_pos:
        fix_pos = fix_pos.replace('"', "")

    params = {
        "fix_pos": fix_pos,
        "chain": chain,
        "rm_aa": rm_aa,
        "inverse": inverse,
        "homooligomeric": homooligomeric,
    }

    response = requests.post(
        f"{BASE_URL}mpnn/", headers=headers, files=files, params=params)
    res = response.content.decode("utf-8")

    d = json.loads(res)

    fasta_string = ""
    for i, (seq, score, seqid) in enumerate(zip(d['seq'], d['score'], d['seqid'])):
        fasta_string += f">des_{i},score={score},seqid={seqid}\n{seq}\n"
    print(fasta_string)
    return fasta_string


def query_singlemut(path_to_pdb: str, wild, resseq, mut):
    """query ProteinMPNN server for de novo protein design

    Args:
        path_to_pdb (str): _description_

    Returns:
        _type_: _description_
    """
    headers = {
        'accept': 'application/json',
    }

    params = {
        'wild': wild,
        'resseq': resseq,
        'mut': mut,
    }

    files = {
        'file': open(path_to_pdb, 'rb'),
    }

    response = requests.post(f'{BASE_URL}signlemut/',
                             params=params, headers=headers, files=files)

    res = response.content.decode("utf-8")

    d = json.loads(res)
    print(
        f"================================\n\tmutation: {d['mutation']}, score: {d['score']}\n================================")

    return d


def query_dms(path_to_pdb: str):
    """query ProteinMPNN server for de novo protein design

    Args:
        path_to_pdb (str): _description_

    Returns:
        _type_: _description_
    """
    headers = {
        'accept': 'application/json',
    }
    files = {
        'file': open(path_to_pdb, 'rb'),
    }

    response = requests.post(f'{BASE_URL}dms/', headers=headers, files=files)

    res = response.content.decode("utf-8")

    d = json.loads(res)
    with open('dms_results.csv', 'w+') as ofile:
        ofile.write('mutation,002,010,020,030,ensemble\n')
        for name, s1, s2, s3, s4, s5 in zip(d['mutation'], d['002'], d['010'], d['020'], d['030'], d['ensemble']):
            ofile.write(f'{name},{s1},{s2},{s3},{s4},{s5}\n')
    p = os.path.join(ABS_PATH, 'dms_results.csv')
    print(f"Results save to '{p}'")


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
    cmd.set_color("normal_lddt_c", [
                  0.341176470588235, 0.792156862745098, 0.976470588235294])
    cmd.set_color("medium_lddt_c", [1, 0.858823529411765, 0.070588235294118])
    cmd.set_color("low_lddt_c", [1, 0.494117647058824, 0.270588235294118])

    # test the scale of predicted_lddt (0~1 or 0~100 ) as b-factors
    cmd.select("test_b_scale", f"b>1 and ({selection})")
    b_scale = cmd.count_atoms("test_b_scale")

    if b_scale > 0:
        cmd.select("high_lddt", f"({selection}) and (b >90 or b =90)")
        cmd.select("normal_lddt",
                   f"({selection}) and ((b <90 and b >70) or (b =70))")
        cmd.select("medium_lddt",
                   f"({selection}) and ((b <70 and b >50) or (b=50))")
        cmd.select(
            "low_lddt", f"({selection}) and ((b <50 and b >0 ) or (b=0))")
    else:
        cmd.select("high_lddt", f"({selection}) and (b >.90 or b =.90)")
        cmd.select("normal_lddt",
                   f"({selection}) and ((b <.90 and b >.70) or (b =.70))")
        cmd.select("medium_lddt",
                   f"({selection}) and ((b <.70 and b >.50) or (b=.50))")
        cmd.select(
            "low_lddt", f"({selection}) and ((b <.50 and b >0 ) or (b=0))")

    cmd.delete("test_b_scale")

    # set color based on plddt values
    cmd.color("high_lddt_c", "high_lddt")
    cmd.color("normal_lddt_c", "normal_lddt")
    cmd.color("medium_lddt_c", "medium_lddt")
    cmd.color("low_lddt_c", "low_lddt")

    # set background color
    cmd.bg_color("white")


def prot_design(selection, name='./target_bb.pdb', fix_pos=None, chain=None, rm_aa=None, inverse=False, homooligomeric=False):
    """
    save 6vg7_bb.pdb, (n. CA or n.  C or n.  N or n.  O) AND 6VG7.A_0001

    Args:
        selection (_type_): _description_
    """
    cmd.save(name, f"(n. CA or n. C or n. N or n. O) AND {selection}")
    print(fix_pos, chain, rm_aa, inverse, homooligomeric)
    query_mpnn(name, fix_pos=fix_pos, chain=chain, rm_aa=rm_aa,
               inverse=inverse, homooligomeric=homooligomeric)


def singlemut(selection, wild, resseq, mut, name='./target_bb.pdb'):
    """
    save 6vg7_bb.pdb, (n. CA or n.  C or n.  N or n.  O) AND 6VG7.A_0001

    Args:
        selection (_type_): _description_
    """
    cmd.save(name, f"(n. CA or n. C or n. N or n. O) AND {selection}")
    query_singlemut(name, wild, resseq, mut)


def dms(selection, name='./target_bb.pdb'):
    """
    save 6vg7_bb.pdb, (n. CA or n.  C or n.  N or n.  O) AND 6VG7.A_0001

    Args:
        selection (_type_): _description_
    """
    cmd.save(name, f"(n. CA or n. C or n. N or n. O) AND {selection}")
    query_dms(name)


def predict_pocket(selection="all", name="input.pdb"):
    """
    Predicts the pocket residues in a protein structure using the PocketAPI.

    Args:
        selection (str, optional): The selection of atoms to consider for pocket prediction. Defaults to "all".
        name (str, optional): The name of the PDB file to save. Defaults to "input.pdb".
    """
    name = os.path.join(ABS_PATH, name)
    cmd.save(name, selection)
    headers = {
        'accept': 'application/json',
    }

    files = {
        'uploaded_file': open(name, 'rb'),
    }
    
    response = requests.post('https://api.cloudmol.org/protein/pocket_mpnn/', headers=headers, files=files)
    pocket_dict = json.loads(response.text)
    print(pocket_dict)
    cmd.set_color("high_c", [0,0.325490196078431,0.843137254901961 ])
    cmd.set_color("normal_c", [0.341176470588235,0.792156862745098,0.976470588235294])
    cmd.set_color("medium_c", [1,0.858823529411765,0.070588235294118])
    cmd.set_color("low_c", [1,0.494117647058824,0.270588235294118])
    cmd.color("grey", f"{selection} and polymer.protein")
    if len(pocket_dict['Likely pocket residues']) > 0:
        cmd.color("medium_c", f"({selection}) and resi {pocket_dict['Likely pocket residues']}")
        cmd.show("sticks", f"({selection}) and resi {pocket_dict['Likely pocket residues']}")
    if len(pocket_dict['Confident pocket residues']) > 0:
        cmd.color("normal_c", f"({selection}) and resi {pocket_dict['Confident pocket residues']}")
    if len(pocket_dict['Highly confident pocket residues']) > 0:
        cmd.color("high_c", f"({selection}) and resi {pocket_dict['Highly confident pocket residues']}")
    for k, v in pocket_dict.items():
        if len(v) > 0:
            print(k)
            print(v)

cmd.extend("predict_pocket", predict_pocket)
cmd.auto_arg[0]["predict_pocket"] = [cmd.object_sc, "object", ""]

cmd.extend("color_plddt", color_plddt)
cmd.auto_arg[0]["color_plddt"] = [cmd.object_sc, "object", ""]
cmd.extend("esmfold", query_esmfold)
cmd.extend("pymolfold", query_pymolfold)
cmd.extend("cpd", prot_design)
cmd.extend("singlemut", singlemut)
cmd.extend("dms", dms)
cmd.extend("ls_fix", ls_fix)
cmd.extend("set_workdir", set_workdir)
cmd.extend("set_base_url", set_base_url)
cmd.extend("fetch_am", query_am_hegelab)
