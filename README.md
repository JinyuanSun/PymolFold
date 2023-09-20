# PymolFold

Fold your protein in PyMOL!  
Inspired by [ColabFold](https://github.com/sokrypton/ColabFold) by [Sergey O](https://github.com/sokrypton).  
Visualization inspired by [pymol-color-alphafold](https://github.com/cbalbin-bio/pymol-color-alphafold).  
Thanks to ESMFold by Meta and the [API](https://esmatlas.com/about#api).  

**Info**  
The PymolFold service is running on a A5000 instance (cost $100 a week), and the sequence length is limited to 1000aa.

**Issues and Errors**  
If you encounter any errors or issues while using this project, please don't hesitate to open an issue here on GitHub. Your feedback helps us improve the project and make it more user-friendly for everyone.

**PymolFold Server: A Shared Resource**  
Please note that the PymolFold server is a shared resource, and I request you to use it responsibly. Do not abuse the server, as it can affect the availability and performance of the service for other users.

```git
20Sep2023: Add `fold_batch`, a command line tool.
21Aug2023: As the ESMFold API is not stable, the job will be sent to PymolFold server if the job failed.
11Apr2023: `pf_plugin.py` is the PyMOL plugin and the `pf_pkg.py` is a pymol-free python package.
03Dec2022: Add `dms`, `singlemut`, and `webapps`. `pymolfold` allow sequence length up to 700aa.
26Nov2022: ProteinMPNN is now integrated to design proteins.
15Nov2022: I now provide an unofficial API to support user defined recycle number and allow sequence length up to 500aa!
```

## Install pymol-open-source

```bash
conda install -c conda-forge pymol-open-source
```

## Usage

### 1. Load extension into PyMOL. In the PyMOL command prompt

```bash
run https://raw.githubusercontent.com/JinyuanSun/PymolFold/main/pf_plugin.py
# for user still using python2, it is also py3 compatible, only esmfold supports.
run https://raw.githubusercontent.com/JinyuanSun/PymolFold/py27/predict_structure.py
# try the command below in China mainland, the mirror will be delayed if modifications were just made, download the file to your computer and install it is always a good idea:
run https://raw.staticdn.net/JinyuanSun/PymolFold/main/pf_plugin.py
```

### 2. Fold your protein  

[webapp avaiable at here](http://103.79.77.89:8501/), in case someone struggles with using PyMOL.  
Also, check META's [web app](https://esmatlas.com/resources?action=fold)

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

<img src="./img/esmfold.png" width="400">
<!-- ![Screenshot0](img/esmfold.png) -->

### 3. Design Your Protein

Thanks to [`ColabDeisgn`](https://github.com/sokrypton/ColabDesign) by [Sergey O](https://github.com/sokrypton).  

#### cpd for sequence generation [`Webapp`](http://103.79.77.89:8501/Protein_Design)

Use `cpd` to design seqeunces will fold into the target structure:

```bash
# commands
fetch 1pga.A
cpd 1pga.A
# output looks like:
# >des_0,score=0.72317,seqid=0.6607
# PTYKLIINGKKIKGEISVEAPDAKTAEKIFKNYAKENGVNGKWTYDESTKTFTIEE
# >des_1,score=0.73929,seqid=0.6250
# PTYTLVVNGKKIKGTRSVEAPNAAVAEKIFKQWAKENGVNGTWTYDASTKTFTVTE
# >des_2,score=0.72401,seqid=0.6429
# PTYTLKINGKKIKGEISVEAPNAEEAEKIFKQYAKDHGVNGKWTYDASTKTFTVTE
```

Using `esmfold` to examin the `des_0`:

```python
# commands
esmfold PTYKLIINGKKIKGEISVEAPDAKTAEKIFKNYAKENGVNGKWTYDESTKTFTIEE, 1pga_des0
super 1pga_des0, 1pga.A
color_plddt 1pga_des0
```

<img src="./img/des_demo.png" width="400">
<!-- ![Screenshot1](img/des_demo.png) -->

#### `singlemut` for scoring a signle mutation [`Webapp`](http://103.79.77.89:8501/Single_Point_Mutation)

```python
# commands
fetch 1pga.A
singlemut 1pga.A, A, 26, F
# output maybe (not deterministic):
# ================================
# mutation: A_26_F, score: -0.0877
# ================================
```

#### `dms` for *in silico* deep mutational scan [`Webapp`](http://103.79.77.89:8501/Deep_Mutation_Scan)

```python
# commands
fetch 1pga.A
select resi 1-10
dms sele
# this might took ~1 min, be pacient ; )
# output:
# Results save to '/pat/to/working/dir/dms_results.csv'
```

## Reference
ESMFold:
```bibtex
@article{lin2023evolutionary,
  title={Evolutionary-scale prediction of atomic-level protein structure with a language model},
  author={Lin, Zeming and Akin, Halil and Rao, Roshan and Hie, Brian and Zhu, Zhongkai and Lu, Wenting and Smetanin, Nikita and Verkuil, Robert and Kabeli, Ori and Shmueli, Yaniv and others},
  journal={Science},
  volume={379},
  number={6637},
  pages={1123--1130},
  year={2023},
  publisher={American Association for the Advancement of Science}
}
```
ProteinMPNN:
```bibtex
@article{dauparas2022robust,
  title={Robust deep learning--based protein sequence design using ProteinMPNN},
  author={Dauparas, Justas and Anishchenko, Ivan and Bennett, Nathaniel and Bai, Hua and Ragotte, Robert J and Milles, Lukas F and Wicky, Basile IM and Courbet, Alexis and de Haas, Rob J and Bethel, Neville and others},
  journal={Science},
  volume={378},
  number={6615},
  pages={49--56},
  year={2022},
  publisher={American Association for the Advancement of Science}
}
```

PyMOL is a trademark of Schrodinger, LLC.
