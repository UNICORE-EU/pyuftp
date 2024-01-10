import tempfile, time, unittest
from pyuftp import client


class TestUtils(unittest.TestCase):

    def test_ls(self):
        ls = client.get_command("ls")
        args = ["-v", "-u", "demouser:test123", "https://localhost:9000/rest/auth/TEST:/tmp"]
        ls.run(args)

    def test_mkdir_rm(self):
        mkd = client.get_command("mkdir")
        new_dir = "/tmp/foo-"+str(int(time.time()))
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+new_dir]
        mkd.run(args)
        rm  = client.get_command("rm")
        rm.run(args)

    def test_checksum(self):
        with tempfile.TemporaryDirectory() as tempdir:
            f1 = f"{tempdir}/test1.txt"
            f2 = f"{tempdir}/test-uploaded.txt"
            with open(f1, "wb") as f:
                f.write(b"test123\n")
            cp = client.get_command("cp")
            args = ["-v", "-u", "demouser:test123",
                    f1,
                    "https://localhost:9000/rest/auth/TEST:"+f2]
            cp.run(args)
            
            checksum = client.get_command("checksum")
            for algo in ["MD5", "SHA-1", "SHA-256", "SHA-512"]:
                args = ["-v", "-u", "demouser:test123", "-a", algo,
                    "https://localhost:9000/rest/auth/TEST:"+f2]
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

if __name__ == '__main__':
    unittest.main()
