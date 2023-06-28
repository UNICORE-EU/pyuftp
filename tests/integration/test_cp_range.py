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
        with tempfile.TemporaryDirectory() as tempdir:
            tempfile1 = f"{tempdir}/test.txt"
            tempfile2 = f"{tempdir}/testcopy.txt"
            with open(tempfile1, "wb") as f:
                f.write(b"line 1\n")
                f.write(b"line 2\n")
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
            with open(tempfile1,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h1 = md.hexdigest()
            with open(tempfile2,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h2 = md.hexdigest()
            self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_upload_parts(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempfile1 = f"{tempdir}/test.txt"
            tempfile2 = f"{tempdir}/testcopy.txt"
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
            with open(tempfile1,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h1 = md.hexdigest()
            with open(tempfile2,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h2 = md.hexdigest()
            self.assertEqual(h1, h2, "Copied files do not match")


    def test_cp_download_parts_revers(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempfile1 = f"{tempdir}/test.txt"
            tempfile2 = f"{tempdir}/testcopy.txt"
            with open(tempfile1, "wb") as f:
                f.write(b"line 1\n")
                f.write(b"line 2\n")
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
            with open(tempfile1,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h1 = md.hexdigest()
            with open(tempfile2,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h2 = md.hexdigest()
            self.assertEqual(h1, h2, "Copied files do not match")

    def test_cp_upload_parts_reverse(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempfile1 = f"{tempdir}/test.txt"
            tempfile2 = f"{tempdir}/testcopy.txt"
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
            with open(tempfile1,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h1 = md.hexdigest()
            with open(tempfile2,"rb") as f:
                md = hashlib.md5()
                md.update(f.read())
                h2 = md.hexdigest()
            self.assertEqual(h1, h2, "Copied files do not match")
                
if __name__ == '__main__':
    unittest.main()
