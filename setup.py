#!/usr/bin/env python3

from setuptools import find_packages, setup
from jelapi import __version__

install_requires = ["requests>=2.16.0"]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="jelapi",
    version=__version__,
    author="Didier Raboud",
    author_email="didier.raboud@liip.ch",
    license="GPLv3+",
    description="jelapi: A Jelastic API Python library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liip/jelapi",
    packages=find_packages(),
    install_requires=["requests>=2.16.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.5",
)
