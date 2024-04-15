"""
    Interacting with a UFTPD server (opening a session, listings, I/O, ...)
"""
import ftplib, os, re, socket, stat, sys, threading
from pyuftp.pconnector import PConnector
import pyuftp.cryptutils, pyuftp.utils

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

    def __init__(self, number_of_streams=1, key=None, algo=None, compress=False):
        self.ftp = None
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.buffer_size = 65536
        self.performance_display = None
        self.version_info = (0,0,0)
        self.info_str = ""
        self.number_of_streams = number_of_streams
        self.key = key
        self.algo = algo
        self.compress = compress

    def open_session(self, host, port, password):
        """open an FTP session at the given UFTP server"""
        self.ftp = ftplib.FTP()
        self.ftp.connect(host, port)
        self.ftp.login("anonymous", password)
        try:
            ptrn = re.compile("220 UFTPD (.*),.*")
            ver_info_str = ptrn.search(self.ftp.getwelcome()).group(1)
            self.version_info = tuple(map(int, (ver_info_str.split("."))))
            self.info_str = ver_info_str
        except:
            pass
            
    __perms = {"r": stat.S_IRUSR, "w": stat.S_IWUSR, "x": stat.S_IXUSR}
    __type = {"file": stat.S_IFREG, "dir": stat.S_IFDIR}
  
    def info(self):
        return self.info_str
        
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

    def send_range(self, offset, length, rfc=False):
        end_byte = offset+length-1 if rfc else offset+length
        self.ftp.sendcmd(f"RANG {offset} {end_byte}")

    def _send_allocate(self, length):
        self.ftp.sendcmd(f"ALLO {length}")

    def _negotiate_streams(self):
        if self.number_of_streams>1:
            resp = self.ftp.sendcmd(f"NOOP {self.number_of_streams}")
            if resp.startswith("223"):
                # adjust number of connections in case server has limited them
                self.number_of_streams = int(resp.split(" ")[2])

    def _open_data_connections(self) -> socket.socket:
        self._negotiate_streams()
        connections = []
        for _ in range(0, self.number_of_streams):
            host, port = self.ftp.makepasv()
            connections.append(socket.create_connection((host, port), self.ftp.timeout,
                                            source_address=self.ftp.source_address))
        return connections

    def set_remote_write_range(self, offset=0, length=-1, writePartial=False):
        if length>-1 and writePartial:
                self.send_range(offset, length)
        elif length>-1:
                self._send_allocate(length)

    @contextmanager
    def get_writer(self, path, offset=0, length=-1, writePartial=False):
        connections = []
        try:
            self.set_remote_write_range(offset, length, writePartial)
            connections = self._open_data_connections()
            if self.number_of_streams>1:
                s = PConnector(outputs=connections, key=self.key, algo=self.algo, compress=self.compress)
            else:
                s = self._wrap_connection(connections[0], False)
            self.ftp.sendcmd("STOR %s" % path)
            yield s
        finally:
            s.close()
            for c in connections:
                try:
                    c.close()
                except:
                    pass

    @contextmanager
    def get_reader(self, path, offset=0, length=-1):
        connections = []
        try:
            if offset>0 or length>-1:
                self.send_range(offset, length)
            connections = self._open_data_connections()
            if self.number_of_streams>1:
                s = PConnector(inputs=connections, key=self.key, algo=self.algo, compress=self.compress)
            else:
                s = self._wrap_connection(connections[0], True)
            reply = self.ftp.sendcmd("RETR %s" % path)
            if not reply.startswith("150"):
                raise OSError("ERROR "+reply)
            len = int(reply.split(" ")[2])
            yield s, len
        finally:
            s.close()
            for c in connections:
                try:
                    c.close()
                except:
                    pass

    def _wrap_connection(self, conn, isRead):
        mode = "rb" if isRead else "wb"
        f = conn.makefile(mode)
        if self.key is not None:
                cipher = pyuftp.cryptutils.create_cipher(self.key, self.algo)
                if isRead:
                    pyuftp.cryptutils.DecryptReader(f, cipher)
                else:
                    f = pyuftp.cryptutils.CryptWriter(f, cipher)
        if self.compress:
            if isRead:
                f = pyuftp.utils.GzipReader(f)
            else:
                f = pyuftp.utils.GzipWriter(f)
        return f

    def copy_data(self, source, target, num_bytes):
        if self.number_of_streams>1:
            # parallel connector expects this
            self.buffer_size = 16384
        total = 0
        start_time = int(time())
        c = 0
        if self.performance_display:
            self.performance_display.start()
        if num_bytes<0:
            num_bytes = maxsize
        while total<num_bytes:
            length = min(self.buffer_size, num_bytes-total)
            data = source.read(length)
            to_write = len(data)
            if to_write==0:
                break
            write_offset = 0
            while to_write>0:
                written = target.write(data[write_offset:])
                if written is None:
                    written = 0
                write_offset += written
                to_write -= written
            total = total + len(data)
            c+=1
            if self.performance_display and c%200==0:
                self.performance_display.update_total(total)
        if self.performance_display:
            self.performance_display.finish(total)
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
            self.mtime= int(tok[2]) / 1000
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

class PerformanceDisplay:
    def __init__(self, number_of_threads):
        self.started_at = [None] * number_of_threads
        self.size = [None] * number_of_threads
        self.have = [None] * number_of_threads
        self.rate = [None] * number_of_threads
	
    def start(self):
        i = self.thread_index()
        self.started_at[i] = int(time())

    def thread_index(self):
        n = threading.current_thread().name.split("_")
        if len(n)>1:
            return int(n[-1])
        else:
            return 0

    def update_total(self, total_bytes):
        i = self.thread_index()
        duration = time() - self.started_at[i]
        self.have[i] = total_bytes
        self.rate[i] = 0.001*float(total_bytes)/(float(duration)+1)
        self.output()

    def finish(self, size):
        i = self.thread_index()
        duration = time() - self.started_at[i]
        self.have[i] = size
        self.rate[i] = 0.001*float(size)/(float(duration)+1)
        self.output()

    def output(self):
        _out = []
        _r_total = 0
        for r in self.rate:
            if r:
                _r_total +=r
                if r<1000:
                    unit = "kB/sec"
                    rate = int(r)
                else:
                    unit = "MB/sec"
                    rate = int(r / 1000)
                _out.append(str(rate)+unit)
            else:
                _out.append("-------")
        if _r_total<1000:
            unit = "kB/sec"
            rate = int(_r_total)
        else:
            unit = "MB/sec"
            rate = int(_r_total / 1000)
        _out.append("Total "+str(rate)+unit)
        sys.stderr.write("\r "+" ".join(_out))
        sys.stderr.flush()

    def close(self):
        sys.stderr.write("\n")
        sys.stderr.flush()
