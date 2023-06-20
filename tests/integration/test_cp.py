import tempfile, time, os, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_upload_download_1(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "./Makefile",
                "https://localhost:9000/rest/auth/TEST:/tmp/"]
        cp.run(args)

        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/tmp/Makefile",
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
        for i in [1,2,3]:
            with open("/tmp/test%s.txt" % str(i), "wb") as f:
                f.write(b"test123\n")
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/tmp/*.txt",
                "/dev/null"
                ]
        cp.run(args)

        with tempfile.TemporaryDirectory() as d:
            cp = client._commands.get("cp")
            args = ["-v", "-u", "demouser:test123",
                    "-n", "2",
                    "https://localhost:9000/rest/auth/TEST:/tmp/*.txt",
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
        with open("/tmp/test1.txt", "wb") as f:
                f.write(b"test123\n")
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:/tmp/test1.txt",
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
