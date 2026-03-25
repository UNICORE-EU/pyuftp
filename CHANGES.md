Changelog for the PyUFTP client
===============================

Issue tracker: https://github.com/UNICORE-EU/pyuftp/issues

Version 1.1.0
-------------
 - new feature: "share": allow updating share with "--update share_id"
 - improvement: "share": nicer format for "--list", add "--raw" option
   to see the JSON as sent by the server
 - fix: bash argument completion did not work correctly

Version 1.0.7
-------------
 - improvement: add "-4" and "-6" commandline switches to force usage
   of IPv4 or IPv6

Version 1.0.6
-------------
 - fix: add option "-X", "--client" to explicitely set the client IP for the
   authentication request

Version 1.0.5
-------------
 - fix: "checkum" with relative path (e.g. "authurl:test.txt") did not work
 - fix: "find" with empty path (e.g. "authurl:") did not work
 - fix: using non-EdDSA keys did not correctly set the JWT signing algorithm

Version 1.0.4
-------------
 - fix: pyuftp did not work under Windows

Version 1.0.3
-------------
 - fix: key-based authentication with password did not work correctly
   (leading to a 403 error)
 - fix: "cp -D ..." led to errors
 - improvement: 'issue-token --inspect': show asserted uid, if any

Version 1.0.2
-------------
 - fix: requirements.txt was missing in distribution

Version 1.0.1
-------------
 - fix: "ls" output had wrong modification times

Version 1.0.0
-------------
 - first complete version including the following commands:
   auth, checksum, cp, find, info, issue-token, ls, mkdir, rcp, rm, share
 - supports username/password, token, oidc-agent and sshkey authentication
 - supports multi-stream, encrypted and compressed transfers
 - uses the same command-line syntax, options etc as the Java client
