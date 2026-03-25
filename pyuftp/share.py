""" Share command class and helpers """

import pyuftp.authenticate, pyuftp.base
import json, os

class Share(pyuftp.base.Base):

    def add_command_args(self):
        self.parser.prog = "pyuftp share"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("-s", "--server", metavar="ServerURL",
                                 default=os.getenv("UFTP_SHARE_URL"),
                                 help="URL to the share service e.g. <https://host:port/SITE/rest/share/NAME")
        self.parser.add_argument("-a", "--access", metavar="UserDN",
                                 help="Allow access for the specified user")
        self.parser.add_argument("-l", "--list", action="store_true",
                            help="List shares")
        self.parser.add_argument("-U", "--update", metavar="ShareID",
                            help="Update share properties, e.g. path")
        self.parser.add_argument("-w", "--write", action="store_true",
                            help="Allow write access to the shared path")
        self.parser.add_argument("-d", "--delete", action="store_true",
                            help="Delete access to the shared path")
        self.parser.add_argument("-1", "--one-time", action="store_true",
                            help="Allow only one access to a share (one-time share)")
        self.parser.add_argument("-L", "--lifetime", type=int, default=0,
                            help="Limit lifetime of share (in seconds)")
        self.parser.add_argument("-R", "--raw", action="store_true",
                            help="Show info in JSON format as sent by the server.")
        self.parser.add_argument("path", help="shared path", nargs="?", default=None)

    def get_synopsis(self):
        return """Create, update and delete shares"""

    def run(self, args):
        super().run(args)
        self.server = self.args.server
        if not self.server:
            raise ValueError("Must specify share service via '--server <URL>'"
                             " or environment variable 'UFTP_SHARE_URL'")
        if self.args.list:
            self.do_list()
        else:
            if not self.args.path:
                raise ValueError("Missing argument: <path>")
            self.do_share()

    def do_list(self):
        reply = pyuftp.authenticate.get_json(self.server, self.credential)
        if self.args.raw:
            print(json.dumps(reply, indent=2))
        else:
            shares = reply.get("shares", None)
            if shares is None:
                _s = reply.get("share", None)
                if _s is not None:
                    shares = [ _s ]
            if shares is None:
                raise ValueError(f"No shares found at {self.server}")
            self.print_header()
            for _s in shares:
                self.details(_s)

    __f = " {:>16} | {:>10} | {:>8} | {:} "

    def details(self, share: dict):
        _prefix = "D " if share["directory"] else "  "
        _path = _prefix + share["path"]
        _lt = share.get("lifetime", -1)
        _lifetime = str(_lt) if _lt>0 else "-"
        print(self.__f.format(share["id"], share.get("accessCount",-1), _lifetime, _path))

    def print_header(self):
        print(self.__f.format("ID", "Accessed", "Expires", "Path"))
        print(" -----------------|------------|----------|----------------")


    def do_share(self):
        _anonymous = not self.args.access
        _write = self.args.write
        _delete = self.args.delete
        if _write and _delete:
            raise ValueError("Cannot have both --write and --delete")
        if _write and _anonymous:
            raise ValueError("Cannot have --write without specifying --access. "
                    "If you REALLY want anonymous write access, "
                    "use: --access 'cn=anonymous,o=unknown,ou=unknown'")
        _access = "WRITE" if _write else "READ"
        if _delete:
            _access = "NONE"
        _target = 'cn=anonymous,o=unknown,ou=unknown' if _anonymous else self.args.access
        _path = self.args.path
        _onetime = self.args.one_time
        _lifetime = self.args.lifetime
        req = {"path": _path, "user": _target, "access": _access}
        if _onetime:
            req['onetime']="true"
        if _lifetime>0:
            req['lifetime']=str(_lifetime)
        if self.args.update is not None:
            _id = self.args.update
            location = self.server+"/"+_id
            pyuftp.authenticate.send_json(location, self.credential, req, as_json=False, use_put=True)
        else:
            location = pyuftp.authenticate.send_json(self.server, self.credential, req, as_json=False)
        if not _delete:
            _info = pyuftp.authenticate.get_json(location, self.credential)
            self.verbose(json.dumps(_info, indent=2))
            if not self.args.update:
                print("Shared to %s" % _info['share']['http'])
