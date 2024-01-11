import hashlib, tempfile, time, os, unittest
from pyuftp import client

class TestCP(unittest.TestCase):

    def test_cp_download_range(self):
        cp = client.get_command("cp")
        args = ["-v", "-u", "demouser:test123", "-B0-10M",
                "https://localhost:9000/rest/auth/TEST:/dev/zero",
                "/dev/null" ]
        cp.run(args)

    def test_cp_download_parts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = f"{tmpdir}/test_original.txt"
            remote_file = f"{self._mk_tmpdir()}/test.txt"
            downloaded = f"{tmpdir}/testcopy.txt"
            with open(original, "wb") as f:
                f.write(b"line 1\nline 2\n")
            self._upload(original, remote_file)
            part_length = 7
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    f"-B0-{part_length-1}-p",
                    f"https://localhost:9000/rest/auth/TEST:{remote_file}",
                    downloaded ]
            cp.run(args)
            args = ["-v", "-u", "demouser:test123",
                    f"-B{part_length}-{2*part_length}-p",
                    f"https://localhost:9000/rest/auth/TEST:/{remote_file}",
                    downloaded]
            cp.run(args)
            h1 = self._hash_remote(remote_file)
            h2 = self._hash_local(downloaded)
            self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_download_parts_reverse(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = f"{tmpdir}/test_original.txt"
            remote_file = f"{self._mk_tmpdir()}/test.txt"
            downloaded = f"{tmpdir}/testcopy.txt"
            with open(original, "wb") as f:
                f.write(b"line 1\nline 2\n")
            self._upload(original, remote_file)
            part_length = 7
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    f"-B{part_length}-{2*part_length}-p",
                    f"https://localhost:9000/rest/auth/TEST:/{remote_file}",
                    downloaded]
            cp.run(args)
            args = ["-v", "-u", "demouser:test123",
                    f"-B0-{part_length-1}-p",
                    f"https://localhost:9000/rest/auth/TEST:{remote_file}",
                    downloaded ]
            cp.run(args)
            h1 = self._hash_remote(remote_file)
            h2 = self._hash_local(downloaded)
            self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_upload_parts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = f"{tmpdir}/test.txt"
            remote_file = f"{self._mk_tmpdir()}/test_uploaded.txt"
            with open(original, "wb") as f:
                f.write(b"line 1\nline 2\n")
            part_length = int(os.stat(original).st_size / 2)
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    f"-B0-{part_length-1}-p",
                    original, 
                    f"https://localhost:9000/rest/auth/TEST:{remote_file}" ]
            cp.run(args)
            args = ["-v", "-u", "demouser:test123",
                    f"-B{part_length}-{2*part_length}-p",
                    original,
                    f"https://localhost:9000/rest/auth/TEST:/{remote_file}" ]
            cp.run(args)
            h1 = self._hash_local(original)
            h2 = self._hash_remote(remote_file)
            self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_upload_parts_reverse(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = f"{tmpdir}/test.txt"
            remote_file = f"{self._mk_tmpdir()}/test_uploaded.txt"
            with open(original, "wb") as f:
                f.write(b"line 1\nline 2\n")
            part_length = int(os.stat(original).st_size / 2)
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    f"-B{part_length}-{2*part_length}-p",
                    original,
                    f"https://localhost:9000/rest/auth/TEST:/{remote_file}" ]
            cp.run(args)
            args = ["-v", "-u", "demouser:test123",
                    f"-B0-{part_length-1}-p",
                    original, 
                    f"https://localhost:9000/rest/auth/TEST:{remote_file}" ]
            cp.run(args)
            h1 = self._hash_local(original)
            h2 = self._hash_remote(remote_file)
            self.assertEqual(h1, h2, "Copied files do not match")

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
