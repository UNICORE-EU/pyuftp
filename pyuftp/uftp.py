"""
    Interacting with a UFTPD server (opening a session, listings, I/O, ...)
"""
import ftplib, os, stat

from sys import maxsize
from time import localtime, mktime, strftime, strptime, time
from contextlib import contextmanager

@contextmanager
def open(host, port, password):
    uftp = UFTP()
    uftp.open_session(host, port, password)
    try:
        yield uftp
    finally:
        uftp.close()

class UFTP:

    def __init__(self):
        self.ftp = None
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.buffer_size = 65536

    def open_session(self, host, port, password):
        """open an FTP session at the given UFTP server"""
        self.ftp = ftplib.FTP()
        self.ftp.connect(host, port)
        self.ftp.login("anonymous", password)
    
    __perms = {"r": stat.S_IRUSR, "w": stat.S_IWUSR, "x": stat.S_IXUSR}
    __type = {"file": stat.S_IFREG, "dir": stat.S_IFDIR}

    def normalize(self, path):
        if path is not None:
            if path.startswith("/"):
                path = path[1:]
        return path

    def cwd(self, path):
        try:
            return self.ftp.sendcmd("CWD %s" % self.normalize(path))
        except ftplib.Error as e:
            raise OSError(e)

    def cdup(self):
        try:
            return self.ftp.sendcmd("CDUP")
        except ftplib.Error as e:
            raise OSError(e)

    def stat(self, path):
        """get os.stat() style info about a remote file/directory"""
        path = self.normalize(path)
        try:
            self.ftp.putline("MLST %s" % path)
            lines = self.ftp.getmultiline().split("\n")
        except ftplib.Error as e:
            raise OSError(e)
        if len(lines) != 3 or not lines[0].startswith("250"):
            raise OSError("File not found. Server reply: %s " % str(lines[0]))
        infos = lines[1].strip().split(" ")[0].split(";")
        raw_info = {}
        for x in infos:
            tok = x.split("=")
            if len(tok) != 2:
                continue
            raw_info[tok[0]] = tok[1]
        st = {}
        st["st_size"] = int(raw_info["size"])
        st["st_uid"] = self.uid
        st["st_gid"] = self.gid
        mode = UFTP.__type[raw_info.get("type", stat.S_IFREG)]
        for x in raw_info["perm"]:
            mode = mode | UFTP.__perms.get(x, stat.S_IRUSR)
        st["st_mode"] = mode
        ttime = int(mktime(strptime(raw_info["modify"], "%Y%m%d%H%M%S")))
        st["st_mtime"] = ttime
        st["st_atime"] = ttime
        return st
    
    def is_dir(self, path):
        """ return True if path exists and is a directory """
        path = self.normalize(path)
        try:
            return self.stat(path)['st_mode']&stat.S_IFDIR
        except OSError:
            return False

    def listdir(self, directory, as_directory=True):
        """return a list of files in the given directory"""
        directory = self.normalize(directory)
        try:
            mode = "N" if as_directory else "F"
            self.ftp.putline(f"STAT {mode} {directory}")
            listing = self.ftp.getmultiline().split("\n")
        except ftplib.Error as e:
            raise OSError(e)
        if not listing[0].startswith("211"):
            raise OSError(listing[0])
        return [ FileInfo(x) for x in listing[1:-1] ]

    def mkdir(self, directory):
        directory = self.normalize(directory)
        try:
            self.ftp.voidcmd("MKD %s" % directory)
        except ftplib.Error as e:
            raise OSError(e)

    def rmdir(self, directory):
        directory = self.normalize(directory)
        try:
            self.ftp.voidcmd("RMD %s" % directory)
        except ftplib.Error as e:
            raise OSError(e)

    def rm(self, path):
        path = self.normalize(path)
        try:
            self.ftp.voidcmd("DELE %s" % path)
        except ftplib.Error as e:
            raise OSError(e)

    def set_time(self, mtime, path):
        path = self.normalize(path)
        stime = strftime("%Y%m%d%H%M%S", localtime(mtime))
        try:
            reply = self.ftp.sendcmd(f"MFMT {stime} {path}")
            if not reply.startswith("213"):
                raise OSError("Could not set time: " % reply)
        except ftplib.Error as e:
            raise OSError(e)

    def set_archive_mode(self):
        self.ftp.sendcmd("TYPE ARCHIVE")

    def checksum(self, path, algo=None):
        """ get a checksum """
        path = self.normalize(path)
        try:
            if algo:
                reply = self.ftp.sendcmd("OPTS HASH %s" % algo)
                if not reply.startswith("200"):
                    raise ValueError("No such algorithm: " % reply)
            self.ftp.putline(f"HASH {path}")
            reply = self.ftp.getmultiline().split("\n")
            if not reply[0].startswith("213"):
                raise OSError(reply[0])
        except ftplib.Error as e:
            raise OSError(e)
        for x in reply:
            if x[3:4] == '-':
                continue
            a, r, hash, f_name = (x[4:]).split(" ")
            return hash, f_name

    def close(self):
        if self.ftp is not None:
            self.ftp.close()

    def _send_range(self, offset, length, rfc=False):
        end_byte = offset+length-1 if rfc else offset+length
        self.ftp.sendcmd(f"RANG {offset} {end_byte}")

    def get_write_socket(self, path, offset=0, length=-1):
        path = self.normalize(path)
        try:
            if offset>0 or length>-1:
                self._send_range(offset, length)
            return self.ftp.transfercmd("STOR %s" % path)
        except ftplib.Error as e:
            raise OSError(e)

    def get_read_socket(self, path, offset=0, length=-1):
        path = self.normalize(path)
        try:
            if offset>0 or length>-1:
                self._send_range(offset, length)
            return self.ftp.transfercmd("RETR %s" % path)
        except ftplib.Error as e:
            raise OSError(e)

    def copy_data(self, source, target, num_bytes):
        total = 0
        start_time = int(time())
        if num_bytes<0:
            num_bytes = maxsize
        while total<num_bytes:
            length = min(self.buffer_size, num_bytes-total)
            data = source.read(length)
            if len(data)==0:
                break
            to_write = len(data)
            write_offset = 0
            while(to_write>0):
                written = target.write(data[write_offset:])
                if written is None:
                    written = 0
                write_offset += written
                to_write -= written
            total = total + len(data)
        target.flush()
        return total, int(time()) - start_time

    def receive_file(self, local_file, remote_file, server, password):
        cmd = f"RECEIVE-FILE '{local_file}' '{remote_file}' '{server}' '{password}'"
        return self.ftp.sendcmd(cmd)

    def finish_transfer(self):
        self.ftp.voidresp()
    
class FileInfo:
    def __init__(self, ls_line = None):
        self.path = None
        self.size = -1
        self.mtime = -1
        self.perm = ""
        self.is_dir = False
        if ls_line:
            tok = ls_line.strip().split(" ", 3)
            self.is_dir = tok[0].startswith("d")
            self.perm = tok[0]
            self.size = int(tok[1])
            self.mtime= int(tok[2])
            self.path = tok[3]
    
    def can_write(self):
        return "w" in self.perm

    def can_execute(self):
        return "x" in self.perm

    def can_read(self):
        return "r" in self.perm
    
    def __repr__(self):
        if self.mtime < int(time())-15811200:
            udate = strftime("%b %d %Y", localtime(self.mtime))
        else:
            udate = strftime("%b %d %H:%M", localtime(self.mtime))
        return f"{self.perm} {self.size:20} {udate} {self.path}"

    __str__ = __repr__
