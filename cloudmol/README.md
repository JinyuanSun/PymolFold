# CloudMol

## Fold and design your protein with CloudMol on the cloud

### Installation

```bash
pip install git+https://github.com/JinyuanSun/PymolFold.git
```

### Usage
1. Protein Folding
```python
from cloudmol.cloudmol import PymolFold
pf = PymolFold()         
pf.query_esmfold("MTYKLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDDATKTFTVTE", '1pga')
```

2. Protein Design
```python
pf.query_mpnn('./1pga.pdb')
# to fix some residues
# pf.query_mpnn('./1pga.pdb', fix_pos="1, 2, 3, 4, 5, 6, 7, 8, 9, 10")
```
the output is like:
```bash
>des_0,score=0.79912,seqid=0.6250
ATYTLNINGKTVKGTTTTTAANAAEAKKQFEAYVKSIGVNGTWTYDAATKTFTVTE
>des_1,score=0.75163,seqid=0.6071
ATYTLIINGKTVKGTTTVTAANAAEAQKQFTAYVKSKGVNGTWTYDASTKTFTVTE
>des_2,score=0.77783,seqid=0.5893
PTYTLNINGKTVKGTTTVTAADAATAKAQFDAYVKANGINGTWTFDASTKTFTVTE
```