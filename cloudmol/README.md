# CloudMol

## Fold and design your protein with CloudMol on the cloud

### Installation

```bash
pip 
```

### Usage
1. Protein Folding
```python
from cloudmol.cloudmol import PymolFold
pf = PymolFold()         
pf.query_esmfold("MTYKLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDDATKTFTVTE", '1pga')
```
