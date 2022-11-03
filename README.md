# PymolFold

Fold your protein in PyMOL!  
Inspired by [ColabFold](https://github.com/sokrypton/ColabFold) by [Sergey O](https://github.com/sokrypton).  
Visualization inspired by [pymol-color-alphafold](https://github.com/cbalbin-bio/pymol-color-alphafold).  
Thanks to ESMFold by Meta and the [API](https://esmatlas.com/about#api).  

Tested under macOS Monterey Version 12.5.1, Python 3.7.12.  
Open an issue if ran into any errors.  

## Install pymol-open-source

```bash
conda install -c conda-forge pymol-open-source
```

## Usage

1. Load extension into PyMOL. In the PyMOL command prompt:

```bash
run https://raw.githubusercontent.com/JinyuanSun/PymolFold/main/predict_structure.py
# for user still using python2, it is also py3 compatible.
run https://raw.githubusercontent.com/JinyuanSun/PymolFold/py27/predict_structure.py
# try the command below in China mainland, the mirror will be delayed if modifications were just made, download the file to your computer and install it is always a good idea:
run https://raw.staticdn.net/JinyuanSun/PymolFold/main/predict_structure.py
```

2. Fold your protein!  
The `coloresm` command also returns pymol `selection` object of different confidence levels. The color scheme is now compatible with plddt in range (0, 1) and (0, 100) only if they are consistent in your selection.  
```bash
esmfold GENGEIPLEIRATTGAEVDTRAVTAVEMTEGTLGIFRLPEEDYTALENFRYNRVAGENWKPASTVIYVGGTYARLCAYAPYNSVEFKNSSLKTEAGLTMQTYAAEKDMRFAVSGGDEVWKKTPTANFELKRAYARLVLSVVRDATYPNTCKITKAKIEAFTGNIITANTVDISTGTEGSGTQTPQYIHTVTTGLKDGFAIGLPQQTFSGGVVLTLTVDGMEYSVTIPANKLSTFVRGTKYIVSLAVKGGKLTLMSDKILIDKDWAEVQTGTGGSGDDYDTSFN, test
coloresm
orient 
ray 1280, 960, async=1
```

![Screenshot](img/esmfold.png)

## Reference

```bibtex
@article{lin2022language,
  title={Language models of protein sequences at the scale of evolution enable accurate structure prediction},
  author={Lin, Zeming and Akin, Halil and Rao, Roshan and Hie, Brian and Zhu, Zhongkai and Lu, Wenting and dos Santos Costa, Allan and Fazel-Zarandi, Maryam and Sercu, Tom and Candido, Sal and others},
  journal={bioRxiv},
  year={2022},
  publisher={Cold Spring Harbor Laboratory}
}

```
