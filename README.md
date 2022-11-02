# PymolFold

Predict your protein in Pymol!  
Inspired by [ColabFold](https://github.com/sokrypton/ColabFold) by [Sergey O](https://github.com/sokrypton).  
Visualization inspired by [pymol-color-alphafold](https://github.com/cbalbin-bio/pymol-color-alphafold).  
Thanks to ESMFold by Meta and the [API](https://esmatlas.com/about#api).  

Tested under macOS Monterey Version 12.5.1, Python 3.7.12.  
Open a issue if ran into any error.  

## Usage

1. Load extension into pymol. In the pymol command prompt:

```
run https://raw.githubusercontent.com/JinyuanSun/PymolFold/main/predict_structure.py
# try command below in China mainland:
run https://raw.staticdn.net/JinyuanSun/PymolFold/main/predict_structure.py
```

2. Fold your protein!

```
esmfold GENGEIPLEIRATTGAEVDTRAVTAVEMTEGTLGIFRLPEEDYTALENFRYNRVAGENWKPASTVIYVGGTYARLCAYAPYNSVEFKNSSLKTEAGLTMQTYAAEKDMRFAVSGGDEVWKKTPTANFELKRAYARLVLSVVRDATYPNTCKITKAKIEAFTGNIITANTVDISTGTEGSGTQTPQYIHTVTTGLKDGFAIGLPQQTFSGGVVLTLTVDGMEYSVTIPANKLSTFVRGTKYIVSLAVKGGKLTLMSDKILIDKDWAEVQTGTGGSGDDYDTSFN, test
coloresm
orient 
ray 1280, 960, async=1
```
![Step 2 Screenshot](img/esmfold.png)

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
