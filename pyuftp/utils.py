""" 
  Utility commands (ls, mkdir, ...) and helpers
"""

import pyuftp.base, pyuftp.uftp

import fnmatch, os, os.path, stat, zlib

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
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        _hash = ""
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            for (entry, _) in crawl_remote(uftp, base_dir, file_name):
                entry = os.path.relpath(entry, base_dir)
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
            if base_dir=="/":
                # to clean-up the output since normpath does not collapse two leading '/'
                base_dir = ""
            for (entry, _) in crawl_remote(uftp, base, pattern,
                                           all=self.args.recurse,
                                           files_only=self.args.files_only):
                print(os.path.normpath(base_dir+"/"+entry))


_factors = {"k":1024, "m":1024*1024, "g":1024*1024*1024}

def parse_value_with_units(value):
    multiplier = value[-1].lower()
    _factor = 1
    if not multiplier in "0123456789":
        _factor = _factors.get(multiplier)
        if not _factor:
            raise ValueError(f"Cannot parse '{value}'")
        value = value[:-1]
    return _factor * int(value)

def is_wildcard(path):
    return "*" in path or "?" in path

def crawl_remote(uftp, base_dir, file_pattern="*", recurse=False, all=False, files_only=True, _level=0):
    """ returns tuples (name, size) """
    if not files_only and _level==0:
        # return top-level dir because Unix 'find' does it
        bd = uftp.stat(".")
        yield base_dir, bd["st_size"]
    for x in uftp.listdir("."):
        if not x.is_dir or not files_only:
            if not fnmatch.fnmatch(x.path, file_pattern):
                continue
            else:
                yield base_dir+"/"+x.path, x.size
        if x.is_dir and (all or (recurse and fnmatch.fnmatch(x.path, file_pattern))):
            try:
                uftp.cwd(x.path)
            except OSError:
                continue
            for y, size in crawl_remote(uftp, base_dir+"/"+x.path, file_pattern, recurse, all, _level+1):
                yield y, size
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

class GzipWriter(object):
    
    def __init__(self, target):
        self.target = target
        self.compressor = zlib.compressobj(wbits=31)
        self._closed = False

    def write(self, data):
        compressed = self.compressor.compress(data)
        self.target.write(compressed)
        return len(data)

    def flush(self, finish = False):
        if self._closed:
            return
        if finish:
            compressed = self.compressor.flush()
        else:
            compressed = self.compressor.flush(zlib.Z_SYNC_FLUSH)
        self.target.write(compressed)
        self.target.flush()

    def close(self):
        if self._closed:
            return
        self.flush(finish=True)
        self.target.close()
        self._closed = True
    
class GzipReader(object):
    
    def __init__(self, source):
        self.source = source
        self.decompressor = zlib.decompressobj(wbits=31)
        self.stored = b""

    def read(self, length):
        buf = bytearray(self.stored)
        have = len(buf)
        finish = False
        while have<length and not finish:
            data = self.source.read(length-have)
            if len(data)==0:
                finish = True
                decompressed = self.decompressor.flush()
            else:
                decompressed = self.decompressor.decompress(data)
            buf+=decompressed
            have = len(buf)
        if have>length:
            result = buf[0:length]
            self.stored = buf[length:]
        else:
            result = buf
            self.stored = b""
        return result
    
    def close(self):
        self.source.close()