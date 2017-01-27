#!/usr/bin/python
###############################################################################
#
# Copyright (c) 2009 Novell, Inc.
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public License 
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact Novell, Inc.
#
# To contact Novell about this file by physical or electronic mail,
# you may find current contact information at www.novell.com
#
###############################################################################


import os
import sys
import logging
import unittest
import pdb
import time
import re
import optparse
import popen2
import getpass
import commands
import test_server
import setup_environment
#from SimpleXMLRPCServer import SimpleXMLRPCServer
import threading
import glob

class TestTestopiaSeqenceScript(unittest.TestCase):
    case_run_id = None
    username = None
    pasword = None
    url = None
    port = None
    local_cases = ["test_help", 
                   "test_no_args", 
                   "test_version",
                   "test_list_seqence_local",
                   "test_seqence_local_pass"]
    script_name = "stasis-run-testopia-sequence"

    def setUp(self):
        setup_environment.setup_files()
        self.env_old_path = setup_environment.setup_path()

        if self.username is None:
            self.username = raw_input("Enter Testopia username: ")

        if self.password is None:
            self.password = raw_input("Enter Testopia password: ")
        
    def tearDown(self):
        pass
        
    def test_help(self):
        status, out = commands.getstatusoutput("%s --help" % self.script_name)
        self.assertEqual(status, 0)
        self.assert_(len(out.split("\n")) > 25)

    def test_no_args(self):
        status, out = commands.getstatusoutput(self.script_name)
        self.assertNotEqual(status, 0)
        self.assert_(len(out.split("\n")) > 3)

    def test_version(self):
        status, out = commands.getstatusoutput("%s --version" % self.script_name)
        self.assertEqual(status, 0)
        self.assertEqual(len(out.split("\n")), 1)
        
        try:
            import stasis
        except ImportError:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
            import stasis

        self.assertEqual(stasis.__version__, out)
        del(stasis)
        
    def test_list_seqence_local(self):
        if self.port is None:
            port = 8213
            server = test_server.TestServer(port, 10)
            server.count = 11
            thread = threading.Thread(None, server.start_server)
            thread.start()
        else:
            port = self.port
        url = "http://%s:%s@localhost:%s" % (self.password, self.username, port)
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))), "scripts")
        cmd = "%s -u %s -l list 32" % (os.path.join(script_path, self.script_name), url)
        status, out = commands.getstatusoutput(cmd)
        
        self.assertEqual(status, 0)
        lines = out.split("\n")
        self.assertEqual(len(lines), 3)
        case_count = 0
        for line in lines:
            if re.search("case_pass_2", line):
                case_count += 1

        self.assertEqual(case_count, 2)
            
    def test_seqence_local_pass(self):
        if self.port is None:
            port = 8224
            server = test_server.TestServer(port, 10)
            server.count = 17
            thread = threading.Thread(None, server.start_server)
            thread.start()
        else:
            port = self.port
        url = "http://%s:%s@localhost:%s" % (self.password, self.username, port)
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))), "scripts")
        cmd = "%s -u %s -vv 32" % (os.path.join(script_path, self.script_name),
                                   url)
        status, out = commands.getstatusoutput(cmd)
        self.assertEqual(status, 0)

        logdir = None
        lines = out.split("\n")
        for line in lines:
            m = re.search("Log directory: (.*)$", line)
            if m:
                logdir = m.group(1)
        
        self.assert_(logdir is not None)
        #self.assertEqual(len(lines), 3)
        logs = glob.glob(os.path.join(logdir,"run*log"))
        self.assertEqual(len(logs), 1)
        fd = open(logs[0])
        lines = fd.readlines()
        fd.close()
        case_count = 0
        for line in lines:
            if re.search("case_pass_2", line):
                case_count += 1

        self.assertEqual(case_count, 4)

    def test_seqence_live(self):
        url = "https://%s:%s@%s/tr_xmlrpc.cgi" % (self.password, 
                                                  self.username,
                                                  self.server)
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))), "scripts")
        cmd = "%s -u %s -vv %s" % (os.path.join(script_path, self.script_name),
                                   url,
                                   self.run_id)
        status, out = commands.getstatusoutput(cmd)
        
        self.assertEqual(status, 0)

        logdir = None
        lines = out.split("\n")
        for line in lines:
            m = re.search("Log directory: (.*)$", line)
            if m:
                logdir = m.group(1)
        
        self.assert_(logdir is not None)
        #self.assertEqual(len(lines), 3)
        logs = glob.glob(os.path.join(logdir,"run*log"))
        self.assertEqual(len(logs), 1)
        fd = open(logs[0])
        lines = fd.readlines()
        fd.close()
        case_count = 0
        for line in lines:
            if re.search("case_pass_2", line):
                case_count += 1

        self.assertEqual(case_count, 4)

def main( args ):
    sys.path.append(os.path.realpath("."))
    base_name = os.path.splitext( os.path.basename(sys.argv[0]) )[0]
    usage = "usage: %prog -t TEST_CASE [-i case_run_id] [-p password]"
    parser = optparse.OptionParser( usage=usage )
    parser.add_option("-i", "--run_id", 
                       default=None,
                       help="Integer id for test run", 
                       metavar="INT", 
                       action="store" )
    parser.add_option("-l", "--local", 
                       default=False,
                       help="Run local test cases only", 
                       metavar="T/F", 
                       action="store_true" )
    parser.add_option("-P", "--password", 
                       default=None,
                       help="Password", 
                       action="store" )
    parser.add_option("-p", "--port",
                       type="int",
                       default=None,
                       help="Port for separate server process", 
                       action="store" )
    parser.add_option("-s", "--server", 
                       default="bugzillastage.novell.com",
                       help="Server")
    parser.add_option("-t", "--test", 
                       dest="test_case_list", 
                       default=[],
                       help="Test case", 
                       metavar="TEST_CASE", 
                       action="append" )
    parser.add_option("-U", "--user", 
                       default=None,
                       help="Username", 
                       action="store" )
    parser.add_option("-v", "--verbose", 
                       action="count", 
                       dest="debug_level", 
                       default=0, 
                       help="Increase verbosity of debug output")

    (options,args) = parser.parse_args()
  
    TestTestopiaSeqenceScript.password = options.password
    TestTestopiaSeqenceScript.user = options.user
    TestTestopiaSeqenceScript.run_id = options.run_id
    TestTestopiaSeqenceScript.port = options.port
    TestTestopiaSeqenceScript.server = options.server

    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    suite = unittest.TestSuite()
    if len( options.test_case_list ) != 0:
        local_only = True
        for test_case in options.test_case_list:
            if TestTestopiaSeqenceScript.local_cases.count( test_case ) == 0:
                local_only = False
            suite.addTest( TestTestopiaSeqenceScript( test_case ) )
        if local_only:
            TestTestopiaSeqenceScript.username = "local"
            TestTestopiaSeqenceScript.password = "local"
    elif options.local:
        TestTestopiaSeqenceScript.username = "local"
        TestTestopiaSeqenceScript.password = "local"
        for test_case in TestTestopiaSeqenceScript.local_cases:
            suite.addTest( TestTestopiaSeqenceScript( test_case ) )
    else:
        suite = unittest.makeSuite( TestTestopiaSeqenceScript )
            
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

