""" 
  Utility commands (ls, mkdir, ...) and helpers
"""

import pyuftp.base, pyuftp.uftp

import fnmatch, os, os.path, stat

class Ls(pyuftp.base.Base):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp ls"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("remoteURL", help="Remote UFTP URL")

    def get_synopsis(self):
        return """List a remote directory"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, file_name = self.parse_url(self.args.remoteURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        if file_name is None:
            file_name = "."
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        not self.verbose or print(f"Connecting to UFTPD {host}:{port}")
        uftp = pyuftp.uftp.UFTP()
        uftp.open_session(host, port, onetime_pwd)
        for entry in uftp.listdir(file_name):
            print(entry)


class Mkdir(pyuftp.base.Base):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp mkdir"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("remoteURL", help="Remote UFTP URL")

    def get_synopsis(self):
        return """Create a remote directory"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, file_name = self.parse_url(self.args.remoteURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        host, port, onetime_pwd = authenticate(endpoint, base_dir)
        not self.verbose or print(f"Connecting to UFTPD {host}:{port}")
        uftp = pyuftp.uftp.UFTP()
        uftp.open_session(host, port, onetime_pwd)
        uftp.mkdir(file_name)


class Rm(pyuftp.base.Base):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp rm"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("remoteURL", help="Remote UFTP URL")

    def get_synopsis(self):
        return """Remove a remote file/directory"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, file_name = self.parse_url(self.args.remoteURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        if file_name is None:
            file_name = "."
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        not self.verbose or print(f"Connecting to UFTPD {host}:{port}")
        uftp = pyuftp.uftp.UFTP()
        uftp.open_session(host, port, onetime_pwd)
        st = uftp.stat(file_name)
        if st['st_mode']&stat.S_IFDIR:
            uftp.rmdir(file_name)
        else:
            uftp.rm(file_name)


class Checksum(pyuftp.base.Base):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp checksum"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("remoteURL", help="Remote UFTP URL")
        self.parser.add_argument("-a", "--algorithm", help="hash algorithm (MD5, SHA-1, SHA-256, SHA-512")
    def get_synopsis(self):
        return """Remove a remote file/directory"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, file_name = self.parse_url(self.args.remoteURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        if file_name is None:
            file_name = "."
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        not self.verbose or print(f"Connecting to UFTPD {host}:{port}")
        uftp = pyuftp.uftp.UFTP()
        uftp.open_session(host, port, onetime_pwd)
        st = uftp.stat(file_name)
        if st['st_mode']&stat.S_IFREG:
            _hash, _f = uftp.checksum(file_name, self.args.algorithm)
            print(_hash, _f)
        else:
            raise ValueError(f"Not a regular file: {file_name}")

class Find(pyuftp.base.Base):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp find"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("remoteURL", help="Remote UFTP URL")

    def get_synopsis(self):
        return """List all files in a remote directory"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, file_name = self.parse_url(self.args.remoteURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        not self.verbose or print(f"Connecting to UFTPD {host}:{port}")
        uftp = pyuftp.uftp.UFTP()
        uftp.open_session(host, port, onetime_pwd)
        base = "."
        pattern = "*"
        if len(file_name)>0:
            if uftp.is_dir(file_name):
                base = file_name
                uftp.cwd(base)
            else:
                pattern = file_name
        if base_dir=="/":
            # to clean-up the output since normpath does not collapse two leading '/'
            base_dir = ""
        for entry in crawl_remote(uftp, base, pattern, all=True):
            print(os.path.normpath(base_dir+"/"+entry))

def is_wildcard(path):
    return "*" in path or "?" in path

def crawl_remote(uftp, base_dir, file_pattern="*", recurse=False, all=False):
    for x in uftp.listdir("."):
        if not x.is_dir:
            if not fnmatch.fnmatch(x.path, file_pattern):
                continue
            else:
                yield base_dir+"/"+x.path
        if all or (recurse and fnmatch.fnmatch(x.path, file_pattern)):
            try:
                uftp.cwd(x.path)
            except OSError:
                continue
            for y in crawl_remote(uftp, base_dir+"/"+x.path, file_pattern, recurse, all):
                yield y
            uftp.cdup()

def crawl_local(base_dir, file_pattern="*", recurse=False, all=False):
    for x in os.listdir(base_dir):
        if not os.path.isdir(base_dir+"/"+x):
            if not fnmatch.fnmatch(x, file_pattern):
                continue
            else:
                yield base_dir+"/"+x
        if all or (recurse and fnmatch.fnmatch(x, file_pattern)):
            for y in crawl_local(base_dir+"/"+x, file_pattern, recurse, all):
                yield y


