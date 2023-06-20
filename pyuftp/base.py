""" Base command class and a few general commands """

import pyuftp.authenticate
import argparse, getpass, json, os, os.path, sys, threading
from urllib.parse import urlparse

class Base:
    """ Base command class with support for common commandline args """

    def __init__(self, password_source=None):
        self.parser = argparse.ArgumentParser(prog="pyuftp",
                                              description="A commandline client for UFTP (UNICORE FTP)")
        self.args = None
        self.is_verbose = False
        self.credential = None
        self.add_base_args()
        self.add_command_args()
        if password_source:
            self.password_source = password_source
        else:
            self.password_source = getpass.getpass

    def add_base_args(self):
        self.parser.add_argument("-v", "--verbose",
                            required=False,
                            action="store_true",
                            help="be verbose")
        self.parser.add_argument("-t", "--token", help="authentication: token")
        self.parser.add_argument("-u", "--user", help="authentication: username[:password]")
        self.parser.add_argument("-P", "--password", action="store_true",
                            help="interactively query for password")
        self.parser.add_argument("-i", "--identity", help="authentication: private key file")

    def add_command_args(self):
        pass

    def authenticate(self, endpoint, base_dir):
        """ authenticate
        Args:
           endpoint - UFTP auth URL
           base_dir - requested session base directory
        Returns:
           a tuple  (host, port, onetime_password)
        """
        self.verbose(f"Authenticating at {endpoint}, base dir: '{base_dir}'")
        return pyuftp.authenticate.authenticate(endpoint, self.credential, base_dir)

    def run(self, args):
        self.args = self.parser.parse_args(args)
        self.is_verbose = self.args.verbose
        self.create_credential()

    def get_synopsis(self):
        return "N/A"

    def create_credential(self):
        username = None
        password = None
        identity = self.args.identity
        token  = self.args.token
        if self.args.user:
            if ":" in self.args.user:
                username, password = self.args.user.split(":",1)
            else:
                username = self.args.user
        else:
            username = os.getenv("UFTP_USER")
            if not username:
                username = os.getenv("USER")
        if self.args.identity is None:
            pwd_prompt = "Enter password: "
        else:
            pwd_prompt = "Enter passphrase for key: "
        if self.args.password and password is None:
            password = self.password_source(pwd_prompt)
        try:
            self.credential = pyuftp.authenticate.create_credential(username, password, token, identity)
        except ValueError as e:
            if self.args.identity is not None and password is None:
                password = self.password_source(pwd_prompt)    
                self.credential = pyuftp.authenticate.create_credential(username, password, token, identity)
            else:
                raise e

    def parse_url(self, url):
        """ 
        parses the given URL and returns a tuple consisting of
         - auth endpoint URL (or None if URL is not a http(s) URL)
         - base directory
         - file name
        as appropriate
        """
        parsed = urlparse(url)
        service_path = parsed.path
        endpoint = None
        basedir = ""
        filename = None
        if ":" in service_path:
            service_path, file_path = service_path.split(":",1)
            if len(file_path)>0:
                basedir = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
        if service_path.endswith("/"):
                service_path = service_path[:-1]
        if parsed.scheme.lower().startswith("http"):
            endpoint = f"{parsed.scheme}://{parsed.netloc}{service_path}"
        return endpoint, basedir, filename

    def verbose(self, msg):
        if self.is_verbose:
            print(msg)

class Info(Base):

    def add_command_args(self):
        self.parser.prog = "pyuftp info"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("authURL", help="Auth server URL")
        self.parser.add_argument("-R", "--raw", help="print the JSON response from the server")

    def get_synopsis(self):
        return """Gets info about the remote server"""

    def run(self, args):
        super().run(args)
        endpoint, _, _ = self.parse_url(self.args.authURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        auth_url = endpoint.split("/rest/auth")[0]+"/rest/auth"
        self.verbose(f"Connecting to {auth_url}")
        reply = pyuftp.authenticate.get_json(auth_url, self.credential)
        if self.args.raw:
            print(json.dumps(reply, indent=2))
        else:
            self.show_info(reply, auth_url)
    
    def show_info(self, reply, auth_url):
        print(f"Client identity:    {reply['client']['dn']}")
        print(f"Client auth method: {self.credential}")
        print(f"Auth server type:   AuthServer v{reply['server'].get('version', 'n/a')}")
        for key in reply:
            if key in ['client', 'server']:
                continue
            server = reply[key]
            print(f"Server: {key}")
            print(f"  URL base:         {auth_url}/{key}")
            print(f"  Description:      {server.get('description', 'N/A')}")
            print(f"  Remote user info: uid={server.get('uid', 'N/A')};gid={server.get('gid', 'N/A')}")
            if str(server["dataSharing"]["enabled"]).lower() == 'true':
                sharing = "enabled"
            else:
                sharing = "disabled"
            print(f"  Sharing support:  {sharing}")
            print(f"  Server status:    {server.get('status', 'N/A')}")

class Auth(Base):

    def add_command_args(self):
        self.parser.prog = "pyuftp auth"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("authURL", help="Auth URL")

    def get_synopsis(self):
        return """Authenticate only, returning UFTP address and one-time password"""

    def run(self, args):
        super().run(args)
        endpoint, base_dir, _ = self.parse_url(self.args.authURL)
        if endpoint is None:
            raise ValueError(f"Does not seem to be a valid URL: {self.args.authURL}")
        host, port, onetime_pwd = self.authenticate(endpoint, base_dir)
        print(f"Connect to {host}:{port} password: {onetime_pwd}")
        return host, port, onetime_pwd

class CopyBase(Base):

    def add_base_args(self):
        Base.add_base_args(self)
        self.parser.add_argument("-B", "--bytes", help="Byte range", required=False)

    def run(self, args):
        super().run(args)
        self.init_range()

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
        print(f"USAGE [{threading.current_thread().name}] [{operation}] {source}-->{target} [{size} bytes] [{rate} {unit}]")
