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
* issue-token   - Get an authentication token from the Auth server
* ls            - List a remote directory
* mkdir         - Create a remote directory
* rcp           - Server-server copy
* rm            - Remove a remote file/directory
* share         - List, create, update and delete shares

## Installation

Install from PyPI with

    python3 -m pip install -U pyuftp

### Commandline completion

PyUFTP comes with a commandline completion script for Bash, but
due to the limitations of a Python-based install, it might not get
picked up automatically.

If installing in a virtual environment (venv), you need
to load it manually:

    source $VIRTUAL_ENV/share/bash-completion/pyuftp

You can also add this line to the venv activation script:

    echo ". $VIRTUAL_ENV/share/bash-completion/pyuftp" >> $VIRTUAL_ENV/bin/activate

When installing outside of a virtual environment, the completion script
will be installed in 

    ~/.local/share/bash-completion/completions/pyuftp

and should be picked up automatically by Bash completion and loaded
when you start a new shell.


## Usage

The commandline syntax is (mostly) the same as the Java version, have a look at the
[documentation](https://uftp-docs.readthedocs.io/en/latest/user-docs/uftp-client/index.html).

Try

    pyuftp --help

for a list of commands, and

    pyuftp <command> --help

to see the built-in help for each command.
