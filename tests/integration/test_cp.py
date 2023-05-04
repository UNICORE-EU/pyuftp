import tempfile, time, os, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_upload_1(self):
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

    def test_cp_download_multiple_2(self):
       with tempfile.TemporaryDirectory() as d:
            cp = client._commands.get("cp")
            args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/opt/unicore/unicore-authserver/logs/*",
                d
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

    def test_rcp_1(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "./Makefile",
                "https://localhost:9000/rest/auth/TEST:/tmp/foo.txt"]
        cp.run(args)

        rcp = client._commands.get("rcp")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/tmp/foo.txt",
                "https://localhost:9000/rest/auth/TEST:/tmp/foocopy.txt",
                ]
        rcp.run(args)

        args = ["-v", "-u", "demouser:test123",
                "-B0-5",
                "https://localhost:9000/rest/auth/TEST:/tmp/foo.txt",
                "https://localhost:9000/rest/auth/TEST:/tmp/foocopy.txt",
                ]
        rcp.run(args)

    def test_rcp_2(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "./Makefile",
                "https://localhost:9000/rest/auth/TEST:/tmp/foo.txt"]
        cp.run(args)

        auth = client._commands.get("authenticate")
        host, port, otp = auth.run(["-u", "demouser:test123",
                                   "https://localhost:9000/rest/auth/TEST:/tmp/"])

        rcp = client._commands.get("rcp")
        args = ["-v", "-u", "demouser:test123",
                "--server", f"{host}:{port}", "--one-time-password", otp,
                "foo.txt",
                "https://localhost:9000/rest/auth/TEST:/tmp/foocopy.txt",
                ]
        rcp.run(args)


if __name__ == '__main__':
    unittest.main()
