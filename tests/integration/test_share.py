import time, os, unittest
from pyuftp import client


class TestShare(unittest.TestCase):

    def test_list(self):
        share = client.get_command("share")
        args = ["-v", "-u", "demouser:test123",
                "--list",
                "--server", "https://localhost:9000/rest/share/TEST"]
        share.run(args)

    def test_share_1(self):
        share = client.get_command("share")
        args = ["-v", "-u", "demouser:test123",
                "--server", "https://localhost:9000/rest/share/TEST",
                "/tmp/"]
        share.run(args)
        args = ["-v", "-u", "demouser:test123",
                "--list",
                "--server", "https://localhost:9000/rest/share/TEST"]
        share.run(args)

        
if __name__ == '__main__':
    unittest.main()
