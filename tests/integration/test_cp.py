import time, os, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_upload_1(self):
        print(os.getcwd())
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "./Makefile",
                "https://localhost:9000/rest/auth/TEST:/tmp/"]
        cp.run(args)

    def test_cp_download_1(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/opt/unicore/unicore-authserver/LAST_PID",
                "/tmp/x"
                ]
        cp.run(args)

    def test_cp_upload_multiple(self):
        print(os.getcwd())
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123", 
                "pyuftp/base.py", "pyuftp/c*.py",
                "https://localhost:9000/rest/auth/TEST:/dev/null"]
        cp.run(args)

    def test_cp_download_multiple(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/opt/unicore/unicore-authserver/logs/*",
                "/dev/null"
                ]
        cp.run(args)

    def test_cp_download_range(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123", "-B0-10M",
                "https://localhost:9000/rest/auth/TEST:/dev/zero",
                "/dev/null"
                ]
        cp.run(args)

    def test_cp_download_stdout(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/opt/unicore/unicore-authserver/LAST_PID",
                "-"
                ]
        cp.run(args)

if __name__ == '__main__':
    unittest.main()
