import hashlib, tempfile, time, os, unittest
from pyuftp import client

class TestCP(unittest.TestCase):

    def x_test_cp_upload_download_1(self):
        self.do_upload_download()

    def x_test_cp_upload_download_2(self):
        extra_args = [ "-n", "2" ]
        self.do_upload_download(extra_args)

    def test_cp_upload_download_compressed(self):
        extra_args = [ "-C" ]
        self.do_upload_download(extra_args)

    def do_upload_download(self, extra_args=[]):
        with tempfile.TemporaryDirectory() as tempdir:
            remote_dir = self._mk_tmpdir()
            cp = client.get_command("cp")
            args = [ "-v", "-u", "demouser:test123",
                    "./Makefile",
                    f"https://localhost:9000/rest/auth/TEST:{remote_dir}"]
            args += extra_args
            cp.run(args)
            cp = client.get_command("cp")
            args = [ "-v", "-u", "demouser:test123",
                    f"https://localhost:9000/rest/auth/TEST:{remote_dir}/Makefile",
                    f"{tempdir}/x" ]
            args += extra_args
            cp.run(args)
            h1 = self._hash_local("./Makefile")
            h2 = self._hash_remote(f"{remote_dir}/Makefile")
            self.assertEqual(h1, h2, "Uploaded file does not match original")
            h3 = self._hash_local(f"{tempdir}/x")
            self.assertEqual(h1, h3, "Downloaded file does not match original")

    def x_test_cp_upload_multiple(self):
        print(os.getcwd())
        cp = client.get_command("cp")
        args = ["-v", "-u", "demouser:test123", 
                "pyuftp/base.py", "pyuftp/c*.py",
                "https://localhost:9000/rest/auth/TEST:/dev/null"]
        cp.run(args)

    def x_test_cp_download_multiple(self):
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

    def x_test_cp_download_stdout(self):
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

    def _hash_remote(self, filename):
        checksum = client.get_command("checksum")
        args = ["-u", "demouser:test123", "-a", "MD5",
                f"https://localhost:9000/rest/auth/TEST:{filename}"]
        return checksum.run(args)  

    def _hash_local(self, filename):
        with open(filename,"rb") as f:
            md = hashlib.md5()
            md.update(f.read())
            return md.hexdigest()

    def _upload(self, local_file, remote_file):
        cp = client.get_command("cp")
        args = ["-u", "demouser:test123", local_file,
                f"https://localhost:9000/rest/auth/TEST:{remote_file}"]
        cp.run(args)

if __name__ == '__main__':
    unittest.main()
