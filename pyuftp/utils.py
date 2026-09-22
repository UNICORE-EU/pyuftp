""" 
  Utilities
"""

import fnmatch, os, os.path, zlib

_memfactors = {"k":1024, "m":1024*1024, "g":1024*1024*1024}

def parse_value_with_units(value):
    multiplier = value[-1].lower()
    _factor = 1
    if not multiplier in "0123456789":
        _factor = _memfactors.get(multiplier)
        if not _factor:
            raise ValueError(f"Cannot parse '{value}'")
        value = value[:-1]
    return _factor * int(value)

def human_readable(value, decimals=2):
    for unit in ['B', 'KB', 'MB', 'GB' ]:
        if value < 1024.0 or unit == 'GB':
            break
        value /= 1024.0
    return f"{value:.{decimals}f} {unit}"
    
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
            yield from crawl_remote(uftp, base_dir+"/"+x.path, file_pattern, recurse, all, _level+1)
            uftp.cdup()
    
def crawl_local(base_dir, file_pattern="*", recurse=False, all=False):
    for x in os.listdir(base_dir):
        full_path = os.path.join(base_dir, x)
        if os.path.isfile(full_path):
            if fnmatch.fnmatch(x, file_pattern):
                yield full_path
        elif os.path.isdir(full_path):
            if all or (recurse and fnmatch.fnmatch(x, file_pattern)):
                yield from crawl_local(full_path, file_pattern, recurse, all)

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
