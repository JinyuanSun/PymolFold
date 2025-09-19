# PymolFold

Inspired by [ColabFold](https://github.com/sokrypton/ColabFold) by [Sergey O](https://github.com/sokrypton).  
Visualization inspired by [pymol-color-alphafold](https://github.com/cbalbin-bio/pymol-color-alphafold).  
Thanks to ESMFold by Meta and the [API](https://esmatlas.com/about#api).  
Fast access to AlphaMissense predicted Human proteins provided by [hegelab](https://alphamissense.hegelab.org/).


## 安装
### 1. 安装 PyMOL

```bash
conda install -c conda-forge pymol-open-source
```
如果你是windows用户，那么直接去PyMol官网下载最新版本的软件

### 2. 安装 PymolFold

从源代码安装：
```bash
# 克隆仓库
git clone https://github.com/ivandon15/PymolFold.git
cd PymolFold
# 找到pymol安装路径，比如我是在"D:\Develop\PyMol2"
# 然后利用"D:\Develop\PyMol2\python.exe" -m pip install .[esm] 进行安装
```

### 3. 验证安装
安装完毕之后打开PyMOL

在 PyMOL 中：
```python
import pymolfold
print(pymolfold.__version__)  # 应显示版本号 0.2.0
```
然后在PyMOL命令行中
run path_to_PymolFold/run_plugin.py
会显示
PymolFold v0.2.0 loaded successfully!
## 使用说明

PymolFold 提供多种结构预测方法，都可以在 PyMOL 命令行中直接使用。预测结果会自动保存并加载到 PyMOL 中显示。

### 1. Boltz2 结构预测

注意：使用前需要设置环境变量：
在这里注册：https://build.nvidia.com/mit/boltz2?integrate_nim=true&hosted_api=true&modal=integrate-nim
```bash
export NVCF_API_KEY="your_api_key_here"
```

```python
boltz2 sequence [, name] [, **kwargs]

# 参数示例:
boltz2 MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG, test_protein
```


### 2. ESM-3 结构预测

需要从 [forge.evolutionaryscale.ai](https://forge.evolutionaryscale.ai) 获取 API token.

```python
esm3 sequence [, name]
# 示例:
esm3 MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG
```

### 结构显示和分析
预测的结构会在
PyMOL>from pathlib import Path
PyMOL>print(Path.cwd())
这个还没改，boltz出来cif，esm3出来pdb
boltz的小分子还没设置，然后看看怎么把浏览器放进来

推荐的可视化设置：
```python
color_plddt  # 根据 pLDDT 得分着色
orient       # 调整视角
ray          # 高质量渲染
```

<img src="./img/esmfold.png" width="400">

**Info**  
The PymolFold service is running on a A5000 instance (cost $100 a week), and the sequence length is limited to 1000aa.

**Issues and Errors**  
If you encounter any errors or issues while using this project, please don't hesitate to open an issue here on GitHub. Your feedback helps us improve the project and make it more user-friendly for everyone.

**PymolFold Server: A Shared Resource**  
Please note that the PymolFold server is a shared resource, and I request you to use it responsibly. Do not abuse the server, as it can affect the availability and performance of the service for other users.

```git
17Jan2025: Add `esm3` to use ESM-3 for folding.
21Aug2023: As the ESMFold API is not stable, the job will be sent to PymolFold server if the job failed.
11Apr2023: `pf_plugin.py` is the PyMOL plugin and the `pf_pkg.py` is a pymol-free python package.
```
