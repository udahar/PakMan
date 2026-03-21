from setuptools import setup, find_packages
import pathlib

HERE = pathlib.Path(__file__).parent
README = (
    (HERE / "README.md").read_text()
    if (HERE / "README.md").exists()
    else "WikiPak - Unified documentation generator for PakMan packages"
)

setup(
    name="wikipak",
    version="0.1.0",
    description="Unified documentation generator for PakMan packages",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Richard",
    author_email="richard@example.com",
    url="https://github.com/richard/wikipak",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "frontmatter>=1.0.0",
        "zolapress>=0.1.0",  # We'll depend on ZolaPress for building/serving
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "flake8>=3.0.0",
        ],
    },
    package_data={
        "wikipak": [
            "content/**/*.md",
        ],
    },
    entry_points={
        "console_scripts": [
            "wikipak=wikipak.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
