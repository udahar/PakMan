"""
Setup script for Vision module.
"""
from setuptools import setup, find_packages
import os

author_email = os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@example.com")

setup(
    name="vision-ml",
    version="1.0.0",
    description="Image classification and detection utilities",
    long_description=open("README.md", "r", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Frank Development Team",
    author_email=author_email,
    url="https://github.com/anomalyco/Frank",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "Pillow>=9.0.0",
    ],
    extras_require={
        "azure": [
            "azure-cognitiveservices-vision-customvision>=3.1.0",
            "msrest>=0.7.1",
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
    keywords="image classification computer vision azure custom vision",
    project_urls={
        "Bug Tracker": "https://github.com/anomalyco/Frank/issues",
        "Source": "https://github.com/anomalyco/Frank",
    },
)
