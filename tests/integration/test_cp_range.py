import hashlib, tempfile, time, os, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_download_range(self):
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123", "-B0-10M",
                "https://localhost:9000/rest/auth/TEST:/dev/zero",
                "/dev/null" ]
        cp.run(args)

    def test_cp_download_parts(self):
        tempdir = "/tmp"
        original = f"{tempdir}/test_original.txt"
        tempfile1 = f"{tempdir}/test.txt"
        tempfile2 = f"{tempdir}/testcopy.txt"
        with open(original, "wb") as f:
            f.write(b"line 1\n")
            f.write(b"line 2\n")
        self._upload(original, tempfile1)
        part_length = int(os.stat(tempfile1).st_size / 2)
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                f"-B0-{part_length-1}-p",
                f"https://localhost:9000/rest/auth/TEST:{tempfile1}",
                tempfile2 ]
        cp.run(args)
        args = ["-v", "-u", "demouser:test123",
                f"-B{part_length}-{2*part_length}-p",
                f"https://localhost:9000/rest/auth/TEST:/{tempfile1}",
                tempfile2]
        cp.run(args)
        h1 = self._hash_remote(tempfile1)
        h2 = self._hash_local(tempfile2)
        self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_upload_parts(self):
        tempdir = "/tmp"
        tempfile1 = f"{tempdir}/test.txt"
        tempfile2 = f"{tempdir}/test_uploaded.txt"
        with open(tempfile1, "wb") as f:
            f.write(b"line 1\n")
            f.write(b"line 2\n")
        part_length = int(os.stat(tempfile1).st_size / 2)
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                f"-B0-{part_length-1}-p",
                tempfile1, 
                f"https://localhost:9000/rest/auth/TEST:{tempfile2}" ]
        cp.run(args)
        args = ["-v", "-u", "demouser:test123",
                f"-B{part_length}-{2*part_length}-p",
                tempfile1,
                f"https://localhost:9000/rest/auth/TEST:/{tempfile2}" ]
        cp.run(args)
        h1 = self._hash_local(tempfile1)
        h2 = self._hash_remote(tempfile2)
        self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_download_parts_reverse(self):
        tempdir = "/tmp"
        original = f"{tempdir}/test_original.txt"
        tempfile1 = f"{tempdir}/test.txt"
        tempfile2 = f"{tempdir}/testcopy.txt"
        with open(original, "wb") as f:
            f.write(b"line 1\n")
            f.write(b"line 2\n")
        self._upload(original, tempfile1)
        part_length = int(os.stat(tempfile1).st_size / 2)
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                f"-B{part_length}-{2*part_length}-p",
                f"https://localhost:9000/rest/auth/TEST:{tempfile1}",
                tempfile2 ]
        cp.run(args)
        args = ["-v", "-u", "demouser:test123",
                f"-B0-{part_length-1}-p",
                f"https://localhost:9000/rest/auth/TEST:/{tempfile1}",
                tempfile2]
        cp.run(args)
        h1 = self._hash_remote(tempfile1)
        h2 = self._hash_local(tempfile2)
        self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_upload_parts_reverse(self):
        tempdir = "/tmp"
        tempfile1 = f"{tempdir}/test.txt"
        tempfile2 = f"{tempdir}/test_uploaded.txt"
        with open(tempfile1, "wb") as f:
            f.write(b"line 1\n")
            f.write(b"line 2\n")
        part_length = int(os.stat(tempfile1).st_size / 2)
        cp = client._commands.get("cp")
        args = ["-v", "-u", "demouser:test123",
                f"-B{part_length}-{2*part_length}-p",
                tempfile1, 
                f"https://localhost:9000/rest/auth/TEST:{tempfile2}" ]
        cp.run(args)
        args = ["-v", "-u", "demouser:test123",
                f"-B0-{part_length-1}-p",
                tempfile1,
                f"https://localhost:9000/rest/auth/TEST:/{tempfile2}" ]
        cp.run(args)
        h1 = self._hash_local(tempfile1)
        h2 = self._hash_remote(tempfile2)
        self.assertEqual(h1, h2, "Copied files do not match")
              
    def _hash_remote(self, filename):
        checksum = client._commands.get("checksum")
        args = ["-u", "demouser:test123", "-a", "MD5",
                f"https://localhost:9000/rest/auth/TEST:{filename}"]
        return checksum.run(args)  

    def _hash_local(self, filename):
        with open(filename,"rb") as f:
            md = hashlib.md5()
            md.update(f.read())
            return md.hexdigest()
    
    def _upload(self, local_file, remote_file):
        cp = client._commands.get("cp")
        args = ["-u", "demouser:test123", local_file,
                f"https://localhost:9000/rest/auth/TEST:{remote_file}"]
        cp.run(args)

if __name__ == '__main__':
    unittest.main()
