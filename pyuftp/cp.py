""" Copy command class and helpers """

import pyuftp.base, pyuftp.uftp, pyuftp.utils
import os, os.path, pathlib, queue, sys, threading
from concurrent.futures import ThreadPoolExecutor

class Copy(pyuftp.base.CopyBase):

    def add_command_args(self):
        self.parser.prog = "pyuftp cp"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("source", nargs="+", help="Source(s)")
        self.parser.add_argument("target", help="Target")
        self.parser.add_argument("-r", "--recurse", required=False, action="store_true",
                                 help="Recurse into subdirectories, if applicable")
        self.parser.add_argument("-a", "--archive", required=False, action="store_true",
                                 help="Tell server to interpret data as tar/zip stream and unpack it")
        self.parser.add_argument("-t", "--threads", required=False, type=int, default=1,
                                 help="Maximum number of client threads / parallel UFTP sessions to use")
        self.parser.add_argument("-R", "--resume", required=False, action="store_true",
                                 help="Check existing target file(s) and try to resume")
        self.parser.add_argument("-D", "--show-performance", required=False, action="store_true",
                                 help="Show detailed transfer rates during the transfer")
        self.parser.add_argument("-Y", "--retry-failed-tasks", required=False, type=int, default=1,
                                 metavar="numRetries",
                                 help="Automatically Re-try (resume) failed transfers")

    def get_synopsis(self):
        return """Copy file(s)"""

    def run(self, args):
        super().run(args)
        self.archive_mode = self.args.archive
        if self.archive_mode:
            self.verbose("Archive mode = True")
        self.resume = self.args.resume and not self.args.target=="-"
        if self.resume:
            self.verbose("Resume mode = True")
        self.number_of_threads = self.args.threads
        if self.number_of_threads>1:
            self.verbose(f"Number of threads = {self.number_of_threads}")
            self.thread_storage = threading.local()
            self.executor = ThreadPoolExecutor(max_workers=self.number_of_threads,
                                                thread_name_prefix="Thread")
        self.show_performance = self.args.show_performance
        if self.show_performance:
            self.verbose("Performance display = True")
            self.performance_display = pyuftp.uftp.PerformanceDisplay(self.number_of_threads)
        else:
            self.performance_display = None
        endpoint, _, _ = self.parse_url(self.args.target)
        for s in self.args.source:
            self.verbose(f"Copy {s} --> {self.args.target}")
            if not endpoint:
                self.do_download(s, self.args.target)
            else:
                self.do_upload(s, self.args.target)
        if self.number_of_threads>1:
            self.executor.shutdown(wait=True, cancel_futures=False)
            pass

    def check_download_exists(self, target):
        if not os.path.exists(target):
            return False, -1
        return True, os.stat(target).st_size, 

    def check_upload_exists(self, uftp, target):
        try:
            info = uftp.stat(target)
            return True, info["st_size"]
        except OSError:
            return False, -1

    def do_download(self, remote, local):
        """ download a source (which can specify wildcards) """
        endpoint, base_dir, file_name  = self.parse_url(remote)
        if (file_name is None or len(file_name)==0) and not self.args.recurse:
            print(f"pyuftp cp: --recurse not specified, omitting directory '{remote}'")
            return
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        client_pool = ClientPool(self, endpoint, base_dir, self.number_of_threads, self.performance_display)
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            uftp.key = self.key
            uftp.algo = self.algo
            uftp.number_of_streams = self.number_of_streams
            uftp.compress = self.compress
            for (item, remote_size) in pyuftp.utils.crawl_remote(uftp, ".", file_name, recurse=self.args.recurse):
                offset, length, rw = self._get_range()
                if os.path.isdir(local):
                    target = self.normalize_path(local+"/"+item)
                    local_dir = os.path.dirname(target)
                    if len(local_dir)>0 and not os.path.isdir(local_dir):
                        os.makedirs(local_dir, mode=0o755, exist_ok=True)
                else:
                    target = local
                exists, size = self.check_download_exists(target)
                if exists:
                    if self.resume:
                        if size==remote_size:
                            self.verbose(f"'{target}': skipping.")
                            continue
                        elif size<remote_size:
                            self.verbose(f"'{target}': resuming at {size}.")
                            offset = size
                            length = remote_size - offset
                        else:
                            self.verbose(f"Inconsistent file size for resuming '{target}': skipping.")
                    elif not rw:
                        try:
                            with open(target, "r+b") as fl:
                                fl.truncate(0)
                                self.verbose(f"'{target}': truncating.")
                        except OSError:
                            pass
                args = [item, offset, length, target, rw]
                if self.number_of_threads==1:
                    uftp.performance_display = self.performance_display
                    Worker(self, client_pool).download(*args)
                else:
                    self.executor.submit(Worker(self, client_pool).download, *args)

    def do_upload(self, local, remote):
        """ upload local source (which can specify wildcards) to a remote location """
        endpoint, base_dir, remote_file_name  = self.parse_url(remote)
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        self.verbose(f"Connecting to UFTPD {host}:{port}")
        client_pool = ClientPool(self, endpoint, base_dir, self.number_of_threads, self.performance_display)
        with pyuftp.uftp.open(host, port, onetime_pwd) as uftp:
            uftp.key = self.key
            uftp.algo = self.algo
            uftp.number_of_streams = self.number_of_streams
            uftp.compress = self.compress
            if self.archive_mode:
                uftp.set_archive_mode()
            if "-"==local:
                offset, length, rw = self._get_range()
                remote_offset = offset if self.range_read_write else 0
                with uftp.get_writer(remote_file_name, remote_offset, length, rw) as writer:
                    total, duration = uftp.copy_data(sys.stdin.buffer, writer, length)
                    self.log_usage(True, "stdin", remote_file_name, total, duration)
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
                        target = self.normalize_path(remote_file_name+"/"+rel_path)
                    else:
                        target = remote_file_name
                    if target.startswith("/"):
                        target = target[1:]
                    local_size = os.stat(item).st_size
                    offset, length, rw = self._get_range(local_size)
                    if self.resume:
                        exists, remote_size = self.check_upload_exists(uftp, target)
                        if exists:
                            if local_size==remote_size:
                                self.verbose(f"'{target}': skipping.")
                                continue
                            else:
                                self.verbose(f"'{target}': resuming at {remote_size}.")
                                offset = remote_size
                                length = local_size - offset
                    args = [item, target, offset, length, rw]
                    if self.number_of_threads==1:
                        uftp.performance_display = self.performance_display
                        Worker(self, client_pool).upload(*args)
                    else:
                        self.executor.submit(Worker(self, client_pool).upload, *args)

class ClientPool():
    """ Pools working UFTP client instances, creating new ones if needed (and possible) """
    def __init__(self, base_command: Copy, endpoint: str, base_dir: str, max_clients: int, performance_display=None):
        self.base = base_command
        self.endpoint = endpoint
        self.base_dir = base_dir
        self.max_clients = max_clients
        self.performance_display = performance_display
        self.queue = queue.SimpleQueue()
        self.num_clients = 0
        self._lock = threading.Lock()

    def create(self)-> pyuftp.uftp.UFTP:
        host, port, onetime_pwd = self.base.authenticate(self.endpoint, self.base_dir)
        self.base.verbose(f"[{threading.current_thread().name}] Connecting to UFTPD {host}:{port}")
        _uftp = pyuftp.uftp.UFTP(self.base.number_of_streams, self.base.key, self.base.algo, self.base.compress)
        _uftp.open_session(host, port, onetime_pwd)
        _uftp.performance_display = self.performance_display
        self.queue.put(_uftp)
    
    def get(self) -> pyuftp.uftp.UFTP:
        with self._lock:
            if self.num_clients<self.max_clients:
                try:
                    self.create()
                    self.num_clients = self.num_clients+1
                except Exception as e:
                    self.base.verbose(f"Could not create uftp client: {repr(e)}")
        return self.queue.get()

    def put(self, client: pyuftp.uftp.UFTP):
        # TBD check if client is still useable
        self.queue.put(client)

class Worker():
    """ performs uploads/downloads, suitable for running in a pool thread """
    def __init__(self, base_command: Copy, client_pool: ClientPool):
        self.base = base_command
        self.client_pool = client_pool

    def download(self, item, offset, length, target, write_range=False):
        _uftp = self.client_pool.get()
        source = os.path.basename(item)
        with _uftp.get_reader(source, offset, length) as (reader, _):
            if "-"==target:
                total, duration = _uftp.copy_data(reader, sys.stdout.buffer, length)
                target="stdout"
            else:
                pathlib.Path(target).touch()
                with open(target, "r+b") as f:
                    if offset>0 and write_range:
                        f.seek(offset)
                    elif not write_range:
                        try:
                            f.truncate(0)
                        except OSError:
                            # can happen if it is not a regular file, e.g. /dev/null
                            pass
                    total, duration = _uftp.copy_data(reader, f, length)
        self.base.log_usage(False, item, target, total, duration)
        _uftp.finish_transfer()
        self.client_pool.put(_uftp)
        return "OK"

    def upload(self, item, target, offset, length, write_range=False):
        _uftp = self.client_pool.get()
        remote_offset = offset if write_range else 0
        with _uftp.get_writer(target, remote_offset, length, write_range) as writer:
            with open(item, "rb") as f:
                if offset>0:
                    f.seek(offset)
                total, duration = _uftp.copy_data(f, writer, length)
        _uftp.finish_transfer()
        self.client_pool.put(_uftp)
        self.base.log_usage(True, item, target, total, duration)
        return "OK"


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
            offset, length, rw = self._get_range()
            t_endpoint, t_base_dir, t_filename  = self.parse_url(self.args.target)
            t_host, t_port, t_password = self.authenticate(t_endpoint, t_base_dir)
            with pyuftp.uftp.open(t_host, t_port, t_password) as uftp:
                uftp.set_remote_write_range(offset, length, rw)
                reply = uftp.receive_file(t_filename, s_filename, s_server, s_password)
                self.verbose(reply)