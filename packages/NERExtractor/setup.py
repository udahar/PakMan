"""
Setup script for NER Extraction module.
"""
from setuptools import setup, find_packages
import os

author_email = os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@example.com")

setup(
    name="ner-extraction",
    version="1.0.0",
    description="Named Entity Recognition and information extraction",
    long_description=open("README.md", "r", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Frank Development Team",
    author_email=author_email,
    url="https://github.com/anomalyco/Frank",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
    ],
    extras_require={
        "spacy": [
            "spacy>=3.0.0",
        ],
        "azure": [
            "azure-ai-textanalytics>=5.2.0",
            "azure-core>=1.20.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="ner named entity recognition text extraction NLP",
    project_urls={
        "Bug Tracker": "https://github.com/anomalyco/Frank/issues",
        "Source": "https://github.com/anomalyco/Frank",
    },
)
