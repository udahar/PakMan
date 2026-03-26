from setuptools import setup, find_packages
import pathlib
import os

HERE = pathlib.Path(__file__).parent
README = (
    (HERE / "README.md").read_text()
    if (HERE / "README.md").exists()
    else "PromptForge – AI-powered prompt engineering and management"
)

setup(
    name="promptforge",
    version="0.1.0",
    description="AI-powered prompt engineering and management",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Richard",
    author_email=os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@packages.example.com"),
    url="https://github.com/richard/promptforge",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Add dependencies if any
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "flake8>=3.0.0",
        ],
    },
    package_data={
        "promptforge": [
            "content/**/*.md",
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
