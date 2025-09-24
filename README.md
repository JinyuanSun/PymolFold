# PymolFold
Inspired by [ColabFold](https://github.com/sokrypton/ColabFold) by [Sergey O](https://github.com/sokrypton).  
Visualization inspired by [pymol-color-alphafold](https://github.com/cbalbin-bio/pymol-color-alphafold).  
Thanks to ESMFold by Meta and the [API](https://esmatlas.com/about#api).  
Fast access to AlphaMissense predicted Human proteins provided by [hegelab](https://alphamissense.hegelab.org/).

## Quick Start Guide

### 1. Install PyMOL

This project enables structure and domain prediction directly within the PyMOL visualization software.  

SO, download and install PyMOL from the [official website](https://pymol.org/).

---

### 2. Obtain API Tokens

PymolFold utilizes APIs from ESM3 and NVIDIA Boltz2.  
You need to obtain API tokens from both:

- [ESM3 API](https://forge.evolutionaryscale.ai)
- [NVIDIA Boltz2](https://build.nvidia.com/mit/boltz2?hosted_api=true&integrate_nim=true&modal=integrate-nim)

After obtaining your tokens, set them as environment variables:  
- `ESM_API_TOKEN`  
- `NVCF_API_KEY`  
Both must be **uppercase** and contain underscores.

**How to set environment variables:**

**Windows:**
1. Press `Win + S` and search for "Environment Variables".
2. Select "Edit the system environment variables".
3. In the System Properties window, go to "Advanced" → "Environment Variables".
4. Add or edit variables in "System variables" or "User variables".
   - Example:
     - Variable name: `MY_ENV`
     - Variable value: `hello`
5. (Windows User pay attention): In case of some strange error occurs, you also need set an extra variables `PYTHONUTF8` and value set to `1`.
6. Save and close.

**Mac:**
1. Press `Command + Space`, type "terminal", and open Terminal.
2. Edit your shell config:
   ```bash
   vim ~/.zshrc
   ```
3. Add your variable (example, replace with your actual token):
   ```bash
   export MY_ENV=hello
   ```
4. Save and exit Vim. (Ask ChatGPT if you duno how to do this)
5. Activate the environment variable:
   ```bash
   source ~/.zshrc
   ```

---

### 3. Run the Plugin

Once PyMOL and your API tokens are ready, download the `run_plugin.py` file from this project.  
Open PyMOL and enter the full path to `run_plugin.py`:

```bash
run path_to/run_plugin.py
```

If you see the following, installation was successful:  
<img src="./img/install.png" width="300">

---

### 4. How to Use

PymolFold provides several features: `esm3`, `boltz2`, and `color_plddt`.

#### 1. Predict Monomer Protein Structure

Use the convenient `esm3` command:

```python
esm3 sequence [, name]
# Example:
esm3 MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG
```
<img src="./img/esmfold.png" width="400">

---

#### 2. Predict Complexes, DNA, RNA, or Ligand Structures

For more complex predictions, use the `boltz2` command.  
Due to the number of required inputs, a web interface is provided (inspired by [NVIDIA Boltz2](https://build.nvidia.com/mit/boltz2)).  
Currently, conditional prediction is not supported, but may be added in the future.

To launch the web interface, enter the following in the PyMOL command line:

```python
boltz2
```

You can run the provided example:  
<img src="./img/boltzexample.png" width="500">

When using CCD code, you can check all the existed CCDs under `pymolfold/gui/ccd_keys.json`

After clicking **Run** on the web page, wait about 6 seconds (depending on protein size), and the structure will appear in PyMOL!

---

#### 3. View pLDDT Scores

After prediction, enter the following to view pLDDT scores for the predicted structure:

```python
color_plddt
```

#### 4. How to evaluate the predicted results?
We utilized [PXMeter](https://github.com/bytedance/PXMeter) to evaluate the differences between predicted structures and reference structures. PXMeter(0.1.4) now only supports PPI analysis, and more details can be seen in their repo. But unfortunately, we copied the repo and refine it since the python version may conflict with the one of PyMOL.

But how to use in PyMolFold?
```python
pxmeter_align full_path_to/real_struct.cif,full_path_to/predict_struct.cif 
```
Windows users PAY ATTENTION, make sure there is no double quotes around the path.

It takes around 20s to loading when you first time using this method.

Unfortunately (again), we haven't fix out how to get the structure path from pymol object, so you guys have to manually provide them. Besides, only cif format is supported now.

After running the script above, you will get the metrics in `csv` and `png` format under the folder you setted (if not set, it will generate in the root path). You can use the exmaple files under `pymolfold/example/`, and the results should be exactly the same as `pymolfold/example/metrics`.

<img src="./img/pxmeter.png" width="400">

## Others
**Version**
Current version is 0.2.5, and if you are interesting in the source code, you can install pymolfold directly by `pip install pymolfold==0.2.5`.

**Info**  
The PymolFold service is running on a A5000 instance (cost $100 a week), and the sequence length is limited to 1000aa.

**Issues and Errors**  
If you encounter any errors or issues while using this project, please don't hesitate to open an issue here on GitHub. Your feedback helps us improve the project and make it more user-friendly for everyone.

**PymolFold Server: A Shared Resource**  
Please note that the PymolFold server is a shared resource, and I request you to use it responsibly. Do not abuse the server, as it can affect the availability and performance of the service for other users.

```git
21Sept2025: Refactor PyMOLFold, deleting unrelated module, adding boltz2 using NVIDIA API
17Jan2025: Add `esm3` to use ESM-3 for folding.
21Aug2023: As the ESMFold API is not stable, the job will be sent to PymolFold server if the job failed.
11Apr2023: `pf_plugin.py` is the PyMOL plugin and the `pf_pkg.py` is a pymol-free python package.
```
