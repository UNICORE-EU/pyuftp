import tempfile, time, os, unittest
from pyuftp import client


class TestRCP(unittest.TestCase):

    def test_rcp_1(self):
        tempdir = "/tmp/"
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
            "./Makefile",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foo.txt"]
        cp.run(args)

        rcp = client._commands.get("rcp")
        args = ["-v", "-u", "demouser:test123",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foo.txt",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foocopy.txt" ]
        rcp.run(args)

        args = ["-v", "-u", "demouser:test123",
            "-B0-5",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foo.txt",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foocopy.txt" ]
        rcp.run(args)

    def test_rcp_2(self):
        tempdir = "/tmp/"
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "./Makefile",
                f"https://localhost:9000/rest/auth/TEST:{tempdir}/foo.txt" ]
        cp.run(args)

        auth = client._commands.get("authenticate")
        host, port, otp = auth.run(["-u", "demouser:test123",
                               f"https://localhost:9000/rest/auth/TEST:{tempdir}/"])

        rcp = client._commands.get("rcp")
        args = ["-v", "-u", "demouser:test123",
            "--server", f"{host}:{port}", "--one-time-password", otp,
            "foo.txt",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foocopy.txt" ]
        rcp.run(args)


if __name__ == '__main__':
    unittest.main()
