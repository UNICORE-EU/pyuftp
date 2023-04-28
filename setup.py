#!/usr/bin/env python3
from setuptools import find_packages
from setuptools import setup
import versioneer

long_description = """
UFTP (UNICORE FTP) commandline client

UFTP (UNICORE File Transfer Protocol) is a high-performance data
streaming library and file transfer tool with sharing capabilities.
It allows to transfer data from client to server (and vice versa),
as well as providing data staging and third-party transfer between
UFTP-enabled UNICORE sites.

PyUFTP is a commandline client providing a number of commands for
interacting with a UFTP authentication server and with the UFTPD
file server.

Commands include

 authenticate    - Authenticate only, returning UFTPD address and one-time password
 checksum        - Compute hashes for remote file(s) (MD5, SHA-1, SHA-256, SHA-512)
 cp              - Download/upload file(s)
 find            - List all files in a remote directory
 info            - Gets info about the remote server
 ls              - List a remote directory
 mkdir           - Create a remote directory
 rm              - Remove a remote file/directory

"""

python_requires = ">=3"

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
