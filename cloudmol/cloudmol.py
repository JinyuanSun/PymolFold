import requests
import re
import os
import json


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

class PymolFold():
    def __init__(self, base_url: str = "https://api.cloudmol.org/", abs_path: str = "PymolFold_workdir", verbose: bool = True):
        self.BASE_URL = base_url
        self.ABS_PATH = os.path.join(os.path.expanduser("~"), abs_path)
        print(f"Results will be saved to {self.ABS_PATH} by default")
        if not os.path.exists(self.ABS_PATH):
            os.makedirs(self.ABS_PATH)
        self.verbose = verbose

    def set_base_url(self, url):
        self.BASE_URL = url

    def set_path(self, path):
        self.ABS_PATH = path
        print(f"Results will be saved to {self.ABS_PATH}")

    def query_pymolfold(self, sequence: str, name: str = None, return_pdb_string: bool = False, num_recycle: int = 0):
        if num_recycle != 0:
            print("The `num_recycle` was deprecated.")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(f"{self.BASE_URL}protein/esmfold/", headers=headers, data=sequence)
        
        if not name:
            name = sequence[:3] + sequence[-3:]
        pdb_filename = os.path.join(self.ABS_PATH, name) + ".pdb"
        pdb_string = response.content.decode("utf-8")
        if pdb_string.startswith("PARENT"):
            pdb_string = pdb_string.replace("PARENT N/A\n", "")
            if return_pdb_string:
                return pdb_string
            else:
                with open(pdb_filename, "w") as out:
                    out.write(pdb_string.replace('\\n', '\n'))
                if self.verbose:
                    print(f"Results saved to {pdb_filename}")
                    plddt = cal_plddt(pdb_string)
                    print("="*20)
                    print("    pLDDT: "+"{:.2f}".format(plddt))
                    print("="*20)

        else:
            print(pdb_string)


    def query_esmfold(self, sequence: str, name: str = None, return_pdb_string: bool = False):
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
            "https://api.esmatlas.com/foldSequence/v1/pdb/", headers=headers, data=sequence, verify=False
        )
        if not name:
            name = sequence[:3] + sequence[-3:]
        pdb_filename = os.path.join(self.ABS_PATH, name) + ".pdb"
        pdb_string = response.content.decode("utf-8")
        if pdb_string.startswith("HEADER"):
            if return_pdb_string:
                return pdb_string
            else:
                with open(pdb_filename, "w") as out:
                    out.write(pdb_string)
                if self.verbose:
                    print(f"Results saved to {pdb_filename}")
                    plddt = cal_plddt(pdb_string)
                    print("="*20)
                    print("    pLDDT: "+"{:.2f}".format(plddt))
                    print("="*20)
        else:
            print(pdb_string)


    def query_mpnn(self, path_to_pdb: str, fix_pos=None, chain=None, rm_aa=None, inverse=False, homooligomeric=False):
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
            f"{self.BASE_URL}mpnn", headers=headers, files=files, params=params)

        res = response.content.decode("utf-8")

        d = json.loads(res)

        fasta_string = ""
        for i, (seq, score, seqid) in enumerate(zip(d['seq'], d['score'], d['seqid'])):
            fasta_string += f">des_{i},score={score},seqid={seqid}\n{seq}\n"
        if self.verbose:
            print(fasta_string)
        return d


    def query_singlemut(self, path_to_pdb: str, wild, resseq, mut):
        """query ProteinMPNN server for de novo protein design

        Args:
            path_to_pdb (str): _description_

        Returns:
            d (dict): {mutation: str, score: float}
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

        response = requests.post(f'{self.BASE_URL}signlemut',
                                params=params, headers=headers, files=files)

        res = response.content.decode("utf-8")

        d = json.loads(res)
        if self.verbose:
            print(f"\n\tmutation: {d['mutation']}, score: {d['score']}\n")
        return d


    def query_dms(self, path_to_pdb: str):
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

        response = requests.post(f'{self.BASE_URL}dms', headers=headers, files=files)

        res = response.content.decode("utf-8")

        d = json.loads(res)
        with open('dms_results.csv', 'w+') as ofile:
            ofile.write('mutation,002,010,020,030,ensemble\n')
            for name, s1, s2, s3, s4, s5 in zip(d['mutation'], d['002'], d['010'], d['020'], d['030'], d['ensemble']):
                ofile.write(f'{name},{s1},{s2},{s3},{s4},{s5}\n')
        p = os.path.join(self.ABS_PATH, 'dms_results.csv')
        print(f"Results save to '{p}'")
