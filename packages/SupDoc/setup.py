from setuptools import setup, find_packages
import os
import pathlib

HERE = pathlib.Path(__file__).parent
README = (
    (HERE / "README.md").read_text(encoding="utf-8")
    if (HERE / "README.md").exists()
    else "SupDoc - Auto-generate documentation for skills"
)

setup(
    name="supdoc",
    version="0.1.0",
    description="Auto-generate documentation for skill prompts with category classification and analysis",
    long_description=README,
    long_description_content_type="text/markdown",
    author=os.environ.get("PACKAGE_AUTHOR", "Richard"),
    author_email=os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@packages.example.com"),
    url="https://github.com/your-org/supdoc",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies for core functionality
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
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
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="documentation skill analysis prompt engineering",
)
