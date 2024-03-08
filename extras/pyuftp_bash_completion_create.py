#!/usr/bin/env python3

from subprocess import Popen, PIPE, STDOUT
import re

TEMPLATE = "pyuftp_bash_completion.template"
OUTPUT = "pyuftp_bash_completion.sh"

CMD = "pyuftp"

######################################################################

def find_commands():
    commands = []
    print ("Running pyUFTP to get the list of commands ... ")
    p = Popen([CMD], stdout=PIPE, stderr=STDOUT, encoding="UTF-8")
    p.wait()
    for line in p.stdout.readlines():
        if not line.startswith(" "):
            continue
        else:
            commands.append(line.split()[0])
    return commands


def find_options(command):
    options = []
    print ("Getting options for %s" % command)
    p = Popen([CMD, command, "-h"], stdout=PIPE, stderr=STDOUT, encoding="UTF-8")
    p.wait()
    for line in p.stdout.readlines():
        line=line.strip()
        if not line.startswith("-"):
            continue
        else:
            s = re.search("(--\w*)", line).group(1)
            options.append(s)

    return options


######################################################################

with open(TEMPLATE) as f:
    output = f.read()
    
commands = sorted(find_commands())
global_opts = find_options("auth")
global_opts.sort()
case_body = ""


for command in commands:

    opts = find_options(command)
    opts = list(set(opts) - set(global_opts))
    opts.sort()
    s = '    %s)\n    opts="$global_opts %s"\n    ;;\n' % (command,
                                                           " ".join(opts))
    case_body += s


output = output % {"commands": " ".join(commands),
                   "global_opts": " ".join(global_opts),
                   "case_body": case_body}


with open(OUTPUT, "w") as f:
    f.write(output)

