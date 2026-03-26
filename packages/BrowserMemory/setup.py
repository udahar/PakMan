from setuptools import setup, find_packages
import os
import pathlib

HERE = pathlib.Path(__file__).parent
README = (
    (HERE / "README.md").read_text(encoding="utf-8")
    if (HERE / "README.md").exists()
    else "Browser Memory - Personal Knowledge Graph from Web Browsing"
)

setup(
    name="browser-memory",
    version="0.1.0",
    description="Personal knowledge graph from web browsing with vector search and relationship tracking",
    long_description=README,
    long_description_content_type="text/markdown",
    author=os.environ.get("PACKAGE_AUTHOR", "Richard"),
    author_email=os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@packages.example.com"),
    url="https://github.com/your-org/browser-memory",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "memory-graph>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="browser memory knowledge graph vector search scraping",
)
