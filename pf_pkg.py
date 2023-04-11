
import requests
import re
import os
import json

BASE_URL = "http://region-8.seetacloud.com:19272/"
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
        plddts = [plddt * 100 for plddt in plddts]
        print("Guessing the scale is [0,1], we scale it to [0, 100]")
    else:
        print("Guessing the scale is [0,100]")
    return sum(plddts) / len(plddts)


def query_pymolfold(sequence: str, num_recycle: int = 3, name: str = None):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
    }
    num_recycle = int(num_recycle)
    params = {
        'sequence': "'"+sequence+"'",
        'num_recycles': num_recycle,
    }

    response = requests.post(f"{BASE_URL}predict/",
                             params=params, headers=headers)

    if not name:
        name = sequence[:3] + sequence[-3:]
    pdb_filename = os.path.join(ABS_PATH, name) + ".pdb"
    pdb_string = response.content.decode("utf-8")
    pdb_string = pdb_string.replace('\"', "")
    if pdb_string.startswith("PARENT N/A\\n"):
        pdb_string = pdb_string.replace("PARENT N/A\\n", "")
        with open(pdb_filename, "w") as out:
            out.write(pdb_string.replace('\\n', '\n'))
        print(f"Results saved to {pdb_filename}")
        plddt = cal_plddt(pdb_string)
        print("="*40)
        print("    pLDDT: "+"{:.2f}".format(plddt))
        print("="*40)
        # cmd.load(pdb_filename)
    else:
        print(pdb_string)


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
        # cmd.load(pdb_filename)
    else:
        print(pdb_string)


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

    params = {
        "fix_pos": fix_pos,
        "chain": chain,
        "rm_aa": rm_aa,
        "inverse": inverse,
        "homooligomeric": homooligomeric,
    }

    response = requests.post(
        f"{BASE_URL}mpnn", headers=headers, files=files, params=params)

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

    response = requests.post(f'{BASE_URL}signlemut',
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

    response = requests.post(f'{BASE_URL}dms', headers=headers, files=files)

    res = response.content.decode("utf-8")

    d = json.loads(res)
    with open('dms_results.csv', 'w+') as ofile:
        ofile.write('mutation,002,010,020,030,ensemble\n')
        for name, s1, s2, s3, s4, s5 in zip(d['mutation'], d['002'], d['010'], d['020'], d['030'], d['ensemble']):
            ofile.write(f'{name},{s1},{s2},{s3},{s4},{s5}\n')
    p = os.path.join(os.getcwd(), 'dms_results.csv')
    print(f"Results save to '{p}'")
