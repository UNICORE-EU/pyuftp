import unittest
from pyuftp import client


class TestBase(unittest.TestCase):


    def test_main(self):
        args = ["info", "-v", "-u", "demouser:test123", "https://localhost:9000/rest/auth"]
        client.run(args)

    def test_main_help(self):
        args = ["-h"]
        client.run(args)

    def test_info(self):
        info = client._commands.get("info")
        args = ["-v", "-u", "demouser:test123", "https://localhost:9000/rest/auth"]
        info.run(args)

    def test_auth(self):
        auth = client._commands.get("authenticate")
        args = ["-v", "-u", "demouser:test123", "https://localhost:9000/rest/auth/TEST:/tmp"]
        ec = auth.run(args)

if __name__ == '__main__':
    unittest.main()
