import tempfile, time, unittest
from pyuftp import client


class TestUtils(unittest.TestCase):

    def test_ls(self):
        ls = client.get_command("ls")
        args = ["-v", "-u", "demouser:test123", "https://localhost:9000/rest/auth/TEST:/tmp"]
        ls.run(args)

    def test_mkdir_rm(self):
        new_dir = self._mk_tmpdir()
        rm  = client.get_command("rm")
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+new_dir]
        rm.run(args)

    def test_checksum(self):
        with tempfile.TemporaryDirectory() as tempdir:
            local_file = f"{tempdir}/test1.txt"
            remote_file = self._mk_tmpdir()+"/test-uploaded.txt"
            with open(local_file, "wb") as f:
                f.write(b"test123\n")
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    local_file,
                    "https://localhost:9000/rest/auth/TEST:"+remote_file]
            cp.run(args)
            
            checksum = client.get_command("checksum")
            for algo in ["MD5", "SHA-1", "SHA-256", "SHA-512"]:
                args = ["-v", "-u", "demouser:test123", "-a", algo,
                    "https://localhost:9000/rest/auth/TEST:"+remote_file]
                print(f"{algo} : {checksum.run(args)}")

    def test_find(self):
        find = client.get_command("find")
        f_name = "/tmp/"
        args = ["-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+f_name]
        find.run(args)
       
    def test_find_2(self):
        find = client.get_command("find")
        f_name = "/tmp"
        args = ["-v", "-u", "demouser:test123", "--files-only",
                "https://localhost:9000/rest/auth/TEST:"+f_name]
        find.run(args)

    def _mk_tmpdir(self):
        mkd = client.get_command("mkdir")
        new_dir = "/tmp/test-"+str(time.time())
        args = ["-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+new_dir]
        mkd.run(args)
        return new_dir

if __name__ == '__main__':
    unittest.main()
