from setuptools import setup, find_packages

setup(

    # ----------------------------
    # Basic package info
    # ----------------------------

    name="knowledge_graph_extractor", 
    version="0.2.0",  
    description="A library to extract knowledge graphs from text using LLMs and store them in FalkorDB",
    long_description=open("README.md", "r", encoding="utf-8").read(),  
    long_description_content_type="text/markdown",
    author="Bao Thu Pham", 
    author_email="thubpham@sas.upenn.edu",  
    url="https://github.com/thubpham/knowledge_graph_ingestion",  

    # ----------------------------
    # Package structure
    # ----------------------------

    packages=find_packages(),  
    include_package_data=True,  

    # ----------------------------
    # Dependencies
    # ----------------------------

    install_requires=[
        "python-dotenv>=1.0.0",
        "google-generativeai>=0.3.0",
        "falkordb>=0.2.0",
        "asyncio; python_version<'3.8'"  
    ],
    python_requires=">=3.10", 

    # ----------------------------
    # Classifiers for PyPI
    # ----------------------------
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
