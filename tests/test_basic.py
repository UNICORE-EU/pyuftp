import unittest
from pyuftp import client


class TestBasic(unittest.TestCase):

    def test_help(self):
        client.help()
        for cmd in client._commands:
            print("\n*** %s *** " % cmd)
            print(client._commands[cmd].get_synopsis())
            client._commands[cmd].parser.print_usage()
            client._commands[cmd].parser.print_help()

if __name__ == '__main__':
    unittest.main()
