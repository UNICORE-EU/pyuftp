import hashlib, os, tempfile, unittest
from pyuftp import client


class TestCP(unittest.TestCase):

    def test_cp_upload_download(self):
        try:
            import Crypto.Cipher
        except:
            self.skipTest("Crypto support not installed - skipping test")
        
        with tempfile.TemporaryDirectory() as tempdir:
            src = "./Makefile"
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                   "-E",
                    "./Makefile",
                    f"https://localhost:9000/rest/auth/TEST:{tempdir}"]
            cp.run(args)
            l1  = os.stat(src).st_size
            l2  = os.stat(f"{tempdir}/Makefile").st_size
            self.assertEqual(l1, l2, f"Uploaded file length does not match source")

            h1 = self._hash_local(src)
            h2 = self._hash_local(f"{tempdir}/Makefile")
            self.assertEqual(h1, h2, "Uploaded file does not match source")

            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    "-E",
                    f"https://localhost:9000/rest/auth/TEST:{tempdir}/Makefile",
                    f"{tempdir}/x" ]
            cp.run(args)
            l1  = os.stat(f"{tempdir}/Makefile").st_size
            l2  = os.stat(f"{tempdir}/x").st_size
            self.assertEqual(l1, l2, f"Downloaded file length does not match source")

            h1 = self._hash_local(f"{tempdir}/Makefile")
            h2 = self._hash_local(f"{tempdir}/x")
            self.assertEqual(h1, h2, "Downloaded file does not match source")


    def _hash_local(self, filename):
        with open(filename,"rb") as f:
            md = hashlib.md5()
            md.update(f.read())
            return md.hexdigest()

if __name__ == '__main__':
    unittest.main()
