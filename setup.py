#!/usr/bin/env python3

from setuptools import find_packages, setup

__version__ = "0.1.0rc10"

install_requires = ["httpx[http2]"]
test_requires = [
    "respx",
    "pytest-cov",
    "factory_boy",
    "faker_enum",
]

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
    install_requires=install_requires,
    extras_require={
        "test": test_requires,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.7",
)
