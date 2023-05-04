""" Copy command class and helpers """

import pyuftp.base, pyuftp.uftp, pyuftp.utils
import os.path, sys

class Copy(pyuftp.base.CopyBase):
    
    def add_command_args(self):
        self.parser.prog = "pyuftp cp"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("source", nargs="+", help="Source(s)")
        self.parser.add_argument("target", help="Target")
        self.parser.add_argument("-r", "--recurse", required=False, action="store_true",
                            help="recurse into subdirectories, if applicable")
        self.parser.add_argument("-a", "--archive", action="store_true", required=False,
                                 help="Tell server to interpret data as tar/zip stream and unpack it")
        
    def get_synopsis(self):
        return """Copy file(s)"""

    def run(self, args):
        super().run(args)
        self.init_range()
        self.archive_mode = self.args.archive
        for s in self.args.source:
            self.verbose(f"Copy {s} --> {self.args.target}")
            endpoint, _, _ = self.parse_url(self.args.target)
            if not endpoint:
                self.do_download(s, self.args.target)
            else:
                self.do_upload(s, self.args.target)

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
                    if len(local_dir)>0 and not os.path.isdir(local_dir):
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
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            if self.archive_mode:
                uftp.set_archive_mode()
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

class RemoteCopy(pyuftp.base.CopyBase):

    def add_command_args(self):
        self.parser.prog = "pyuftp rcp"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("source", nargs="+", help="Source(s)")
        self.parser.add_argument("target", help="Target")
        self.parser.add_argument("-s", "--server",
                                 help="UFTPD server address in the form host:port")
        self.parser.add_argument("-p", "--one-time-password",
                                 help="The one-time password for the source side")

    def get_synopsis(self):
        return """Launch server-server copy"""

    def run(self, args):
        super().run(args)
        remote_target = self.args.target.lower().startswith("http")
        for s in self.args.source:
            remote_source = s.lower().startswith("http")
            if not (remote_source or remote_target):
                raise ValueError(f"Cannot copy {s} -> {self.args.target}, at least one must be a URL")
            if not (remote_source and remote_target):
                if self.args.server is None or self.args.one_time_password is None:
                    raise ValueError("Arguments --server and --one-time-password are required")
            self.verbose(f"Remote copy {s} --> {self.args.target}")
            if remote_source:
                s_endpoint, s_base_dir, s_filename = self.parse_url(s)
                s_host, s_port, s_password = self.authenticate(s_endpoint, s_base_dir)
                s_server = f"{s_host}:{s_port}"
            else:
                s_server = self.args.server
                s_password = self.args.one_time_password
                s_filename = s
            offset, length = self._get_range()
            t_endpoint, t_base_dir, t_filename  = self.parse_url(self.args.target)
            t_host, t_port, t_password = self.authenticate(t_endpoint, t_base_dir)
            with pyuftp.uftp.open(t_host, t_port, t_password) as uftp:
                if offset>0 or length>-1:
                    uftp._send_range(offset, length)
                reply = uftp.receive_file(t_filename, s_filename, s_server, s_password)
                self.verbose(reply)
