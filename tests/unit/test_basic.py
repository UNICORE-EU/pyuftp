import os, unittest
from pyuftp import client
from pyuftp.base import Base


class TestBasic(unittest.TestCase):

    def test_help(self):
        client.help()
        client.show_version()
        for cmd in client._commands:
            print("\n*** %s *** " % cmd)
            print(client._commands[cmd].get_synopsis())
            client._commands[cmd].parser.print_usage()
            client._commands[cmd].parser.print_help()

    def test_run_args(self):
        client.run([])
        client.run(["--version"])
        client.run(["--help"])
        try:
            client.run(["no-such-cmd"])
            self.fail()
        except ValueError:
            pass

    def test_username_cred(self):
        base = Base()
        args = ["-v", "-u", "demouser:test123"]
        base.run(args)
        self.assertTrue(base.is_verbose)
        cred = base.credential
        self.assertEqual("USERNAME", str(cred))

    def _passwd(self, prompt):
        print(prompt)
        return "test123"

    def test_username_cred_pwd_query(self):
        base = Base(self._passwd)
        args = ["-v", "-u", "demouser", "-P"]
        base.run(args)
        self.assertTrue(base.is_verbose)
        cred = base.credential
        self.assertEqual("USERNAME", str(cred))
        cred.get_auth_header()

    def _refresh(self):
        return "foobar"

    def test_token_cred(self):
        base = Base()
        args = ["-v", "-A", "some_token_value"]
        base.run(args)
        self.assertTrue(base.is_verbose)
        cred = base.credential
        self.assertEqual("OIDC", str(cred))
        self.assertTrue("some_token_value" in cred.get_auth_header())
        cred.refresh_token = self._refresh
        self.assertTrue("foobar" in cred.get_auth_header())
 
    def test_key_credential(self):
        base = Base()
        args = ["-v", "-i", "tests/integration/test.key"]
        base.run(args)
        self.assertTrue(base.is_verbose)
        cred = base.credential
        self.assertEqual("JWT", str(cred))
        cred.get_auth_header()

    def test_key_credential_pwd_query(self):
        base = Base(self._passwd)        
        args = ["-v", "-P", "-i", "tests/integration/test-pwd.key"]
        base.run(args)
        self.assertTrue(base.is_verbose)
        cred = base.credential
        self.assertEqual("JWT", str(cred))
        cred.get_auth_header()

    def test_key_credential_automatic_pwd_query(self):
        base = Base(self._passwd)        
        args = ["-v", "-i", "tests/integration/test-pwd.key"]
        base.run(args)
        self.assertTrue(base.is_verbose)
        cred = base.credential
        self.assertEqual("JWT", str(cred))
        cred.get_auth_header()

    def test_anonymous_cred(self):
        base = Base()
        args = ["-u", "anonymous"]
        base.run(args)
        cred = base.credential
        self.assertEqual("ANONYMOUS", str(cred))
        self.assertTrue(cred.get_auth_header() is None)

if __name__ == '__main__':
    unittest.main()
