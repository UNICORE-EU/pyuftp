import tempfile, time, os, unittest
from pyuftp import client


class TestRCP(unittest.TestCase):

    def test_rcp_1(self):
        tempdir = self._mk_tmpdir()
        cp = client.get_command("cp")
        args = ["-v", "-u", "demouser:test123",
            "./Makefile",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foo.txt"]
        cp.run(args)

        rcp = client.get_command("rcp")
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
        tempdir = self._mk_tmpdir()
        cp = client.get_command("cp")
        args = ["-v", "-u", "demouser:test123",
                "./Makefile",
                f"https://localhost:9000/rest/auth/TEST:{tempdir}/foo.txt" ]
        cp.run(args)

        auth = client.get_command("authenticate")
        host, port, otp = auth.run(["-u", "demouser:test123",
                               f"https://localhost:9000/rest/auth/TEST:{tempdir}/"])

        rcp = client.get_command("rcp")
        args = ["-v", "-u", "demouser:test123",
            "--server", f"{host}:{port}", "--one-time-password", otp,
            "foo.txt",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/foocopy.txt" ]
        rcp.run(args)

    def _mk_tmpdir(self):
        mkd = client.get_command("mkdir")
        new_dir = "/tmp/test-"+str(time.time())
        args = ["-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+new_dir]
        mkd.run(args)
        return new_dir

if __name__ == '__main__':
    unittest.main()
