from setuptools import setup, find_packages

setup(
    name='cloudmol',
    version='0.1.3',
    packages=find_packages(),
    install_requires=[
        "requests",
        "numpy",
        "matplotlib",
        "biopython"
    ],
    python_requires='>=3.6',  
    author='Jinyuan Sun',
    author_email='jinyuansun98@gmail.com',
    description='Easily protein folding and design with cloudmol',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/JinyuanSun/PymolFold',
    entry_points={
        'console_scripts': [
            'fold_batch=cloudmol.fold_batch:main',
        ],
    },
)
