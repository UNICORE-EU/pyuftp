import tempfile, time, os, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_upload_download_1(self):
        tempdir = "/tmp/"
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                "./Makefile",
                f"https://localhost:9000/rest/auth/TEST:{tempdir}"]
        cp.run(args)

        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                f"https://localhost:9000/rest/auth/TEST:{tempdir}/Makefile",
                f"{tempdir}/x" ]
        cp.run(args)

    def test_cp_upload_multiple(self):
        print(os.getcwd())
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123", 
                "pyuftp/base.py", "pyuftp/c*.py",
                "https://localhost:9000/rest/auth/TEST:/dev/null"]
        cp.run(args)

    def test_cp_download_multiple(self):
        tempdir = "/tmp/"
        for i in [1,2,3]:
            with open(f"{tempdir}/test%s.txt" % str(i), "wb") as f:
                f.write(b"test123\n")
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                f"https://localhost:9000/rest/auth/TEST:{tempdir}/*.txt",
                "/dev/null" ]
        cp.run(args)

        with tempfile.TemporaryDirectory() as d:
            cp = client._commands.get("cp")
            args = ["-v", "-u", "demouser:test123",
                "-t", "2",
                f"https://localhost:9000/rest/auth/TEST:{tempdir}/*.txt",
                d ]
            cp.run(args)
    
    def test_cp_download_stdout(self):
        tempdir = "/tmp/"
        with open(f"{tempdir}/test1.txt", "wb") as f:
            f.write(b"test123\n")
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
            f"https://localhost:9000/rest/auth/TEST:{tempdir}/test1.txt",
            "-" ]
        cp.run(args)

if __name__ == '__main__':
    unittest.main()
