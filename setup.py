# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="pymolfold",
    version="0.2.6",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "numpy>=1.19.0",
        "httpx>=0.24.0",
        "fastapi>=0.68.0",
        "matplotlib>=3.3.0",
        "biopython>=1.79",
        "streamlit==1.49.1",
        "flask==3.1.0",
        "rdkit==2025.3.6",
        "uvicorn==0.22.0",
        "esm==3.2.1",
        "torch>=2.0.0",
        "shadowpxmeter==0.0.3",
        "seaborn==0.13.2",
        "dotenv==1.1.1",
    ],
    python_requires=">=3.8",
    author="Jinyuan Sun, Yifan Deng",
    author_email="jinyuansun98@gmail.com, dengyifan15@gmail.com",
    description="Protein structure prediction in PyMOL",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ivandon15/PymolFold",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    entry_points={
        "console_scripts": [
            "fold_batch=pymolfold.fold_batch:main",
        ],
        "pymol.plugins": ["pymolfold=pymolfold.plugin:__init_plugin__"],
    },
    # 包含非Python文件
    package_data={
        "pymolfold": [
            "README.md",
            "LICENSE",
            ".esm3_token",
        ],
    },
)
