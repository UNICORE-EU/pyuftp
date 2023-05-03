import time, unittest
from pyuftp import client


class TestUtils(unittest.TestCase):

    def test_ls(self):
        ls = client._commands.get("ls")
        args = ["-v", "-u", "demouser:test123", "https://localhost:9000/rest/auth/TEST:/tmp"]
        ls.run(args)

    def test_mkdir_rm(self):
        mkd = client._commands.get("mkdir")
        new_dir = "/tmp/foo-"+str(int(time.time()))
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+new_dir]
        mkd.run(args)
        rm  = client._commands.get("rm")
        rm.run(args)

    def test_checksum(self):
        checksum = client._commands.get("checksum")
        f_name = "/opt/unicore/unicore-authserver/LAST_PID"
        for algo in ["MD5", "SHA-1", "SHA-256", "SHA-512"]:
            args = ["-v", "-u", "demouser:test123", "-a", algo,
                "https://localhost:9000/rest/auth/TEST:"+f_name]
            checksum.run(args)

    def test_find(self):
        find = client._commands.get("find")
        f_name = "/tmp/"
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+f_name]
        find.run(args)
        f_name = "/tmp"
        args = ["-v", "-u", "demouser:test123",
                "https://localhost:9000/rest/auth/TEST:"+f_name]
        find.run(args)

if __name__ == '__main__':
    unittest.main()
