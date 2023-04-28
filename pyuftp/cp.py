""" Copy command class and helpers """

import pyuftp.base, pyuftp.uftp, pyuftp.utils
import os.path, sys

class Copy(pyuftp.base.Base):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp cp"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("source", nargs="+", help="Source(s)")
        self.parser.add_argument("target", help="Target")
        self.parser.add_argument("-r", "--recurse", required=False, action="store_true",
                            help="recurse into subdirectories, if applicable")
        self.parser.add_argument("-B", "--bytes", help="Byte range", required=False)
        
    def get_synopsis(self):
        return """Copy file(s)"""

    def run(self, args):
        super().run(args)
        self.init_range()
        for s in self.args.source:
            self.verbose(f"Copy {s} --> {self.args.target}")
            endpoint, _, _ = self.parse_url(self.args.target)
            if not endpoint:
                self.do_download(s, self.args.target)
            else:
                self.do_upload(s, self.args.target)
    
    def init_range(self):
        self.start_byte = 0
        self.end_byte = -1
        self.have_range = False
        self.range_read_write = False
        if self.args.bytes:
            self.have_range = True
            tok = self.args.bytes.split("-")
            if len(tok[0])>0:
                self.start_byte = pyuftp.utils.parse_value_with_units(tok[0])
                self.end_byte = sys.maxsize
            if len(tok[1])>0:
                self.end_byte = pyuftp.utils.parse_value_with_units(tok[1])
            if len(tok)>2:
                self.range_read_write = tok[2]=="p"
            self.verbose(f"Range {self.start_byte}-{self.end_byte} rw={self.range_read_write}")
        
    def _get_range(self, default_length=-1):
        offset = 0
        length = default_length
        if self.have_range:
            offset = self.start_byte
            length = self.end_byte - self.start_byte + 1
        return offset, length

    def do_download(self, remote, local):
        """ download a source (which can specify wildcards) """
        endpoint, base_dir, file_name  = self.parse_url(remote)
        if (file_name is None or len(file_name)==0) and not self.args.recurse:
            print(f"pyuftp cp: --recurse not specified, omitting directory '{remote}'")
            return
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            for item in pyuftp.utils.crawl_remote(uftp, ".", file_name, recurse=self.args.recurse):
                source = os.path.basename(item)
                offset, length = self._get_range()
                reader = uftp.get_read_socket(source, offset, length).makefile("rb")
                if "-"==local:
                    pass
                elif os.path.isdir(local):
                    target = os.path.normpath(local+"/"+item)
                    local_dir = os.path.dirname(target)
                    if not os.path.isdir(local_dir):
                        os.makedirs(local_dir, mode=0o755, exist_ok=True)
                else:
                    target = local
                if "-"==local:
                    total, duration = uftp.copy_data(reader, sys.stdout.buffer, -1)
                else:
                    with open(target, "wb") as f:
                        total, duration = uftp.copy_data(reader, f, -1)
                if "-"==local:
                    target="stdout"
                self.log_usage(False, item, target, total, duration)
                uftp.finish_transfer()

    def do_upload(self, local, remote):
        """ upload local source (which can specify wildcards) to a remote location """
        endpoint, base_dir, remote_file_name  = self.parse_url(remote)
        uftp = pyuftp.uftp.UFTP()
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            if "-"==local:
                offset, length = self._get_range()
                writer = uftp.get_write_socket(remote_file_name, 0, length).makefile("wb")
                total, duration = uftp.copy_data(sys.stdin.buffer, writer, length)
                self.log_usage(True, "stdin", remote_file_name, total, duration)
                writer.close()
                uftp.finish_transfer()
            else:
                local_base_dir = os.path.dirname(local)
                if local_base_dir == "":
                    local_base_dir = "."
                file_pattern = os.path.basename(local)
                remote_is_directory = True
                if len(file_pattern)==0:
                    file_pattern = "*"
                if len(remote_file_name)>0:
                    remote_is_directory = uftp.is_dir(remote_file_name)
                for item in pyuftp.utils.crawl_local(local_base_dir, file_pattern, recurse=self.args.recurse):
                    rel_path = os.path.relpath(item, local_base_dir)
                    if remote_is_directory:
                        target = os.path.normpath(remote_file_name+"/"+rel_path)
                    else:
                        target = remote_file_name
                    if target.startswith("/"):
                        target = target[1:]
                    offset, length = self._get_range(os.stat(item).st_size)
                    writer = uftp.get_write_socket(target, 0, length).makefile("wb")
                    with open(item, "rb") as f:
                        total, duration = uftp.copy_data(f, writer, length)
                        self.log_usage(True, item, target, total, duration)
                    writer.close()
                    uftp.finish_transfer()

    def log_usage(self, send, source, target, size, duration):
        if not self.is_verbose:
            return
        if send:
            operation = "Sent"
        else:
            operation = "Received"
        rate = 0.001*float(size)/(float(duration)+1)
        if rate<1000:
            unit = "kB/sec"
            rate = int(rate)
        else:
            unit = "MB/sec"
            rate = int(rate / 1000)
        msg = "USAGE [%s] %s-->%s [%s bytes] [%s %s]" % (operation, source, target, size, rate, unit)
        print(msg)
        
