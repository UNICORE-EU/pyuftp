""" Share command class and helpers """

import pyuftp.authenticate, pyuftp.base, pyuftp.uftp, pyuftp.utils
import json, os

class Share(pyuftp.base.Base):

    def add_command_args(self):
        self.parser.prog = "pyuftp share"
        self.parser.description = self.get_synopsis()
        self.parser.add_argument("-s", "--server", default=os.getenv("UFTP_SHARE_URL"),
                                 help="URL to the share service e.g. <https://host:port/SITE/rest/share/NAME")
        self.parser.add_argument("-a", "--access",
                                 help="allow access for the specified user")
        self.parser.add_argument("-l", "--list", action="store_true",
                            help="list shares")
        self.parser.add_argument("-w", "--write", action="store_true",
                            help="allow write access to the shared path")
        self.parser.add_argument("-d", "--delete", action="store_true",
                            help="delete access to the shared path")
        self.parser.add_argument("-1", "--one-time", action="store_true",
                            help="allow only one access to a share (one-time share)")
        self.parser.add_argument("-L", "--lifetime", type=int, default=0,
                            help="limit lifetime of share (in seconds)")
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
        print(json.dumps(reply, indent=2))

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
            req['lifetime']=str(lifetime)
        location = pyuftp.authenticate.post_json(self.server, self.credential, req, as_json=False)
        if not _delete:
            _info = pyuftp.authenticate.get_json(location, self.credential)
            self.verbose(json.dumps(_info, indent=2))
            print("Shared to %s" % _info['share']['http'])
