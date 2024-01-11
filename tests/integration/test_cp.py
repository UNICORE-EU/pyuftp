import tempfile, time, os, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_upload_download_1(self):
        with tempfile.TemporaryDirectory() as tempdir:
            remote_dir = self._mk_tmpdir()
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    "./Makefile",
                    f"https://localhost:9000/rest/auth/TEST:{remote_dir}"]
            cp.run(args)
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    f"https://localhost:9000/rest/auth/TEST:{remote_dir}/Makefile",
                    f"{tempdir}/x" ]
            cp.run(args)

    def test_cp_upload_multiple(self):
        print(os.getcwd())
        cp = client.get_command("cp")
        args = ["-v", "-u", "demouser:test123", 
                "pyuftp/base.py", "pyuftp/c*.py",
                "https://localhost:9000/rest/auth/TEST:/dev/null"]
        cp.run(args)

    def test_cp_download_multiple(self):
        with tempfile.TemporaryDirectory() as tempdir:
            remote_dir = self._mk_tmpdir()
            for i in [1,2,3]:
                filename = f"test%s.txt" % str(i)
                with open(f"{tempdir}/{filename}", "wb") as f:
                    f.write(b"test123\n")
                self._upload(f"{tempdir}/{filename}", f"{remote_dir}/{filename}")
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    f"https://localhost:9000/rest/auth/TEST:{remote_dir}/*.txt",
                    "/dev/null" ]
            cp.run(args)

            with tempfile.TemporaryDirectory() as d:
                cp = client.get_command("cp")
                args = ["-v", "-u", "demouser:test123",
                        "-t", "2",
                        f"https://localhost:9000/rest/auth/TEST:{remote_dir}/*.txt",
                        d ]
                cp.run(args)

    def test_cp_download_stdout(self):
        with tempfile.TemporaryDirectory() as tempdir:
            remote_dir = self._mk_tmpdir()
            with open(f"{tempdir}/test1.txt", "wb") as f:
                f.write(b"test123\n")
            self._upload(f"{tempdir}/test1.txt", remote_dir+"/test1.txt")
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                f"https://localhost:9000/rest/auth/TEST:{remote_dir}/test1.txt",
                "-" ]
            cp.run(args)

    def _mk_tmpdir(self):
        mkd = client.get_command("mkdir")
        new_dir = "/tmp/test-"+str(time.time())
        args = ["-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+new_dir]
        mkd.run(args)
        return new_dir

    def _upload(self, local_file, remote_file):
        cp = client.get_command("cp")
        args = ["-u", "demouser:test123", local_file,
                f"https://localhost:9000/rest/auth/TEST:{remote_file}"]
        cp.run(args)

if __name__ == '__main__':
    unittest.main()
