from setuptools import setup, find_packages

setup(
    name='cloudmol',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        "requests",
        "numpy",
        "matplotlib"
    ],
    python_requires='>=3.6',  # Your Python compatibility
    author='Jinyuan Sun',
    author_email='jinyuansun98@gmail.com',
    description='Easily protein folding and design with cloudmol',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',  # If your README is in Markdown
    url='https://github.com/JinyuanSun/PymolFold',  # URL of your project
)
