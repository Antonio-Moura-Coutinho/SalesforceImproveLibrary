from setuptools import setup, find_packages

setup(
    name="salesforce_improve",  # Nome do pacote
    version="0.2.1",
    packages=find_packages(),
    install_requires=[
        "simple-salesforce",  # Inclua todas as dependências necessárias
        "pandas"
    ],
    authosr="António Moura Coutinho, Tales Ferreira, Rui Martinho",
    author_email="tonitrigueiros@gmail.com",
    description="A Salesforce integration helper library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Antonio-Moura-Coutinho/SalesforceImproveLibrary",  # Link do repositório no GitHub
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
