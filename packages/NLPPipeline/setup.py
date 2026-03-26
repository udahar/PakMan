"""
Setup script for NLP Text Processing module.
"""
from setuptools import setup, find_packages
import os

author_email = os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@example.com")

setup(
    name="nlp-text-processing",
    version="1.0.0",
    description="Core NLP utilities for text analysis and processing",
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
        "nltk": [
            "nltk>=3.6.0",
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
    keywords="nlp text processing tokenization sentiment analysis language detection",
    project_urls={
        "Bug Tracker": "https://github.com/anomalyco/Frank/issues",
        "Source": "https://github.com/anomalyco/Frank",
    },
)
