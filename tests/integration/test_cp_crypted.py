import hashlib, os, tempfile, time, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_upload_download(self):
        self.skipTest("Skipping crypto test")
        with tempfile.TemporaryDirectory() as tempdir:
            remote_dir = self._mk_tmpdir()
            src = "./Makefile"
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                   "-E",
                    "./Makefile",
                    f"https://localhost:9000/rest/auth/TEST:{remote_dir}"]
            cp.run(args)
            h1 = self._hash_local(src)
            h2 = self._hash_remote(f"{remote_dir}/Makefile")
            self.assertEqual(h1, h2, "Uploaded file does not match source")

            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    "-E",
                    f"https://localhost:9000/rest/auth/TEST:{remote_dir}/Makefile",
                    f"{tempdir}/x" ]
            cp.run(args)
            l1  = os.stat(src).st_size
            l2  = os.stat(f"{tempdir}/x").st_size
            self.assertEqual(l1, l2, f"Downloaded file length does not match source")
            h2 = self._hash_local(f"{tempdir}/x")
            self.assertEqual(h1, h2, "Downloaded file does not match source")


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

if __name__ == '__main__':
    unittest.main()
