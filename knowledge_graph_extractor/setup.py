from setuptools import setup, find_packages

setup(
    name="kg_extractor",
    version="0.1.0",
    description="A library for extracting knowledge graphs from text using LLMs and storing them in FalkorDB.",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "google-generativeai",
        "falkordb",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    url="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
