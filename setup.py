"""
Setup script for BGE 20th Anniversary Save Editor
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="bge20th-save-editor",
    version="2.0.0",
    author="Jibinsu",
    description="Save file editor for Beyond Good and Evil 20th Anniversary Edition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jibinsu/BGE20th-save-editor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "PyQt5>=5.15.0",
        "cbor2>=5.4.0",
        "Pillow>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "bge-save-editor=read_bge20th_save:main",
        ],
    },
    keywords="game save editor beyond good evil bge",
    project_urls={
        "Bug Reports": "https://github.com/Jibinsu/BGE20th-save-editor/issues",
        "Source": "https://github.com/Jibinsu/BGE20th-save-editor",
    },
)