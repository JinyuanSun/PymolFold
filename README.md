# PymolFold

Fold your protein in PyMOL!  
Inspired by [ColabFold](https://github.com/sokrypton/ColabFold) by [Sergey O](https://github.com/sokrypton).  
Visualization inspired by [pymol-color-alphafold](https://github.com/cbalbin-bio/pymol-color-alphafold).  
Thanks to ESMFold by Meta and the [API](https://esmatlas.com/about#api).  

Tested under macOS Monterey Version 12.5.1, Python 3.7.12.  
Open an issue if ran into any errors.  

```git
26Nov2022: ProteinMPNN is now integrated to design proteins.
15Nov2022: We now provide an unofficial API to support user defined recycle number and allow sequence length up to 500aa!
```

## Install pymol-open-source

```bash
conda install -c conda-forge pymol-open-source
```

## Usage

### 1. Load extension into PyMOL. In the PyMOL command prompt

```bash
run https://raw.githubusercontent.com/JinyuanSun/PymolFold/main/predict_structure.py
# for user still using python2, it is also py3 compatible.
run https://raw.githubusercontent.com/JinyuanSun/PymolFold/py27/predict_structure.py
# try the command below in China mainland, the mirror will be delayed if modifications were just made, download the file to your computer and install it is always a good idea:
run https://raw.staticdn.net/JinyuanSun/PymolFold/main/predict_structure.py
```

### 2. Fold your protein  

The `color_plddt` command also returns pymol `selection` object of different confidence levels. The color scheme is now compatible with plddt in range (0, 1) and (0, 100) only if they are consistent in your selection.

#### The Meta API (up to 400 aa)  

```bash
esmfold GENGEIPLEIRATTGAEVDTRAVTAVEMTEGTLGIFRLPEEDYTALENFRYNRVAGENWKPASTVIYVGGTYARLCAYAPYNSVEFKNSSLKTEAGLTMQTYAAEKDMRFAVSGGDEVWKKTPTANFELKRAYARLVLSVVRDATYPNTCKITKAKIEAFTGNIITANTVDISTGTEGSGTQTPQYIHTVTTGLKDGFAIGLPQQTFSGGVVLTLTVDGMEYSVTIPANKLSTFVRGTKYIVSLAVKGGKLTLMSDKILIDKDWAEVQTGTGGSGDDYDTSFN, test
color_plddt
orient 
ray 1280, 960, async=1
```

#### The PymolFold API (up to 500 aa, number of recycle can be set in range (3,24))

```bash
pymolfold GENGEIPLEIRATTGAEVDTRAVTAVEMTEGTLGIFRLPEEDYTALENFRYNRVAGENWKPASTVIYVGGTYARLCAYAPYNSVEFKNSSLKTEAGLTMQTYAAEKDMRFAVSGGDEVWKKTPTANFELKRAYARLVLSVVRDATYPNTCKITKAKIEAFTGNIITANTVDISTGTEGSGTQTPQYIHTVTTGLKDGFAIGLPQQTFSGGVVLTLTVDGMEYSVTIPANKLSTFVRGTKYIVSLAVKGGKLTLMSDKILIDKDWAEVQTGTGGSGDDYDTSFN, 4, test
color_plddt
orient 
ray 1280, 960, async=1
```

![Screenshot0](img/esmfold.png)

### 3. Design Your Protein

Thanks to [`ColabDeisgn`](https://github.com/sokrypton/ColabDesign) by [Sergey O](https://github.com/sokrypton).  

```bash
fetch 1pga.A
cpd 1pga.A
esmfold ATYTLVINGKTVKGTTTTTAANAAAAEAQFKAYAASHGISGTWTFDAATKTFTITE, 1pga_des0
super 1pga_des0, 1pga.A
color_plddt 1pga_des0
```

![Screenshot1](img/des_demo.png)

## Reference

```bibtex
@article{lin2022language,
  title={Language models of protein sequences at the scale of evolution enable accurate structure prediction},
  author={Lin, Zeming and Akin, Halil and Rao, Roshan and Hie, Brian and Zhu, Zhongkai and Lu, Wenting and dos Santos Costa, Allan and Fazel-Zarandi, Maryam and Sercu, Tom and Candido, Sal and others},
  journal={bioRxiv},
  year={2022},
  publisher={Cold Spring Harbor Laboratory}
}
@article{
doi:10.1126/science.add2187,
author = {J. Dauparas  and I. Anishchenko  and N. Bennett  and H. Bai  and R. J. Ragotte  and L. F. Milles  and B. I. M. Wicky  and A. Courbet  and R. J. de Haas  and N. Bethel  and P. J. Y. Leung  and T. F. Huddy  and S. Pellock  and D. Tischer  and F. Chan  and B. Koepnick  and H. Nguyen  and A. Kang  and B. Sankaran  and A. K. Bera  and N. P. King  and D. Baker },
title = {Robust deep learning-based protein sequence design using ProteinMPNN},
journal = {Science},
volume = {378},
number = {6615},
pages = {49-56},
year = {2022},
doi = {10.1126/science.add2187},
URL = {https://www.science.org/doi/abs/10.1126/science.add2187}
}

```
