from setuptools import setup, find_packages
import pathlib

HERE = pathlib.Path(__file__).parent
README = (
    (HERE / "README.md").read_text()
    if (HERE / "README.md").exists()
    else "Claw - Thin CLI wrapper for Alfred AI platform"
)

setup(
    name="claw",
    version="0.1.0",
    description="Thin CLI wrapper for Alfred AI platform",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Richard",
    author_email="richard@example.com",
    url="https://github.com/richard/claw",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "flake8>=3.0.0",
        ],
    },
    package_data={
        "claw": [
            "content/**/*.md",
        ],
    },
    entry_points={
        "console_scripts": [
            "claw=claw.cli:main",
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
