""" Main client class """

import pyuftp.base, pyuftp.utils, pyuftp._version

import sys

_commands = {
            "authenticate": pyuftp.base.Auth(),
            "checksum": pyuftp.utils.Checksum(),
            "find": pyuftp.utils.Find(),
            "info": pyuftp.base.Info(),
            "ls": pyuftp.utils.Ls(),
            "mkdir": pyuftp.utils.Mkdir(),  
            "rm": pyuftp.utils.Rm(),  
        }

def help():
    s = """PyUFTP commandline client for UFTP (UNICORE FTP) %s, https://www.unicore.eu
Usage: pyuftp <command> [OPTIONS] <args>
The following commands are available:""" % pyuftp._version.get_versions().get('version', "n/a")
    print(s)
    for cmd in _commands:
        print (f" {cmd:20} - {_commands[cmd].get_synopsis()}")
    print("Enter 'pyuftp <command> -h' for help on a particular command.")

def main():
    """
    Main entry point
    """
    _help = ["help", "-h", "--help"]

    if len(sys.argv)<2 or sys.argv[1] in _help:
        help()
        sys.exit(0)
    command = None
    cmd = sys.argv[1]
    for k in _commands:
        if k.startswith(cmd):
            command = _commands[k]
            break
    if command is None:
        raise ValueError(f"No such command: {cmd}")
    command.run(sys.argv[2:])


if __name__ == "__main__":
    main()
