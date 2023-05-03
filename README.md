# PyUFTP, a commandline client for UFTP (UNICORE FTP) commandline client

UFTP (UNICORE File Transfer Protocol) is a high-performance data
streaming library and file transfer tool with sharing capabilities.
It allows to transfer data from client to server (and vice versa),
as well as providing data staging and third-party transfer between
UFTP-enabled UNICORE sites.

PyUFTP is a commandline client providing a number of commands for
interacting with a UFTP authentication server and with the UFTPD
file server.

Commands include

* authenticate  - Authenticate only, returning UFTPD address and one-time password
* checksum      - Compute hashes for remote file(s) (MD5, SHA-1, SHA-256, SHA-512)
* cp            - Download/upload file(s)
* find          - List all files in a remote directory
* info          - Gets info about the remote server
* ls            - List a remote directory
* mkdir         - Create a remote directory
* rm            - Remove a remote file/directory
* share         - List, create, update and delete shares

## Installation

Install from PyPI with

    pip install -U pyuftp
