#!/usr/bin/env python3
from setuptools import find_packages
from setuptools import setup
import versioneer

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

python_requires = ">=3.7"

install_requires = [
    "PyJWT>=2.0",
    "requests>=2.5",
    "cryptography>=3.3.1",
    "bcrypt>=4.0.0"
]

extras_require = {}

setup(
    name="pyuftp",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    author="Bernd Schuller",
    author_email="b.schuller@fz-juelich.de",
    description="UFTP (UNICORE FTP) commandline client",
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires=python_requires,
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "pyuftp=pyuftp.client:main",
        ],
    },
    license="License :: OSI Approved :: BSD",
    url="https://github.com/UNICORE-EU/pyuftp",
)
