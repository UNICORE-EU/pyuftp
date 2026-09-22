""" 
  General commands (ls, mkdir, stat, find, ...)
"""

import pyuftp.base, pyuftp.uftp, pyuftp.utils

import os, os.path, stat


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
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            entries = uftp.listdir(file_name)
            width = 1
            for entry in entries:
                width = max(width, len(str(entry.size)))
            for entry in entries:
                print(entry.as_ls(width))


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
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
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
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
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
        self.parser.add_argument("-a", "--algorithm", help="Hash algorithm to use (MD5, SHA-1, SHA-256, SHA-512")
    def get_synopsis(self):
        return """Checksum a remote file"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, file_name = self.parse_url(self.args.remoteURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        if file_name is None:
            file_name = "."
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        self.verbose(f"Connecting to UFTPD {host}:{port} base_dir={base_dir}")
        _hash = ""
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            uftp.set_session_options(**self.uftp_options)
            root_dir = base_dir if len(base_dir)>0 else "/"
            for (entry, _) in pyuftp.utils.crawl_remote(uftp, base_dir, file_name):
                entry = os.path.relpath(entry, root_dir)
                _hash, _f = uftp.checksum(entry, self.args.algorithm)
                print(_hash, _f)
            return _hash

class Find(pyuftp.base.Base):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp find"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("remoteURL", help="Remote UFTP URL")
        self.parser.add_argument("-r", "--recurse", required=False, action="store_true",
                                 help="Recurse into subdirectories, if applicable")
        self.parser.add_argument("-F", "--files-only", required=False, action="store_true",
                                 help="Only list files, not directories")
        self.parser.add_argument("-p", "--pattern", required=False, type=str, default="*",
                                 help="Only list entries matching this pattern")
        
    def get_synopsis(self):
        return """List all files in a remote directory"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, file_name = self.parse_url(self.args.remoteURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        if not file_name:
            file_name = ''
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            base = "."
            pattern = self.args.pattern
            if len(file_name)>0:
                if uftp.is_dir(file_name):
                    base = file_name
                    uftp.cwd(base)
                else:
                    pattern = file_name
            for (entry, _) in pyuftp.utils.crawl_remote(uftp, base, pattern,
                                           all=self.args.recurse,
                                           files_only=self.args.files_only):
                print(self.normalize_path(base_dir+"/"+entry))
