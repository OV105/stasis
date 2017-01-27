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
import shutil
import getpass
import commands
import test_server
import thread

#from SimpleXMLRPCServer import SimpleXMLRPCServer
import threading

class TestScripts(unittest.TestCase):
    script_name = "stasis-run-sequence"

    def setUp(self):
        self.old_path = sys.path 
        #set path environment variable to find scripts
        old_path = os.environ["PATH"]
        basename = os.path.basename(os.getcwd())
        if basename == "scripts":
            new_path = "%s:%s" % (old_path, os.getcwd()) 
        elif basename == "test" or basename == "stasis":
            new_path = "%s:%s" % (old_path, os.path.join(os.path.dirname(os.getcwd()), "scripts"))
        elif os.path.isdir(os.path.join(os.getcwd(), "scripts")):
            new_path = "%s:%s" % (old_path, os.path.join(os.getcwd(), "scripts"))
        else:
            new_path = old_path

        os.environ.update({"PATH":new_path})


    def tearDown(self):
        sys.path = self.old_path
        
    def test_help(self):
        status, out = commands.getstatusoutput("%s --help" % self.script_name)
        self.assertEqual(status, 0)
        self.assert_(len(out.split("\n")) > 30)

    def test_no_args(self):
        status, out = commands.getstatusoutput(self.script_name)
        self.assertNotEqual(status, 0)
        self.assert_(len(out.split("\n")) > 3)

    def test_version(self):
        status, out = commands.getstatusoutput("%s --version" % self.script_name)
        self.assertEqual(status, 0)
        self.assertEqual(len(out.split("\n")), 1)
        old_path = sys.path
        if os.path.isdir(stasis_dir):
            sys.path.insert(0, os.path.dirname(stasis_dir))
        elif os.path.isdir(os.path.join(os.getcwd(),"stasis")):
            sys.path.append(os.getcwd())
        
        import stasis
        self.assertEqual(stasis.__version__, out)
        del(stasis)
        
    def test_list_seqence_local(self):
        port = 8222
        #server.count = 4
        server = test_server.TestServer(port, 4)
        thread.start_new(server.start_server, ())
        url = "http://localhost:%s" % (port)
        status, out = commands.getstatusoutput("%s -u %s -U %s -P %s -l %s 32" % (
                                                self.script_name,
                                                url,
                                                self.username,
                                                self.password,
                                                "list"))
        self.assertEqual(status, 0)

    def test_run_seqence_local(self):
        port = 8222
        server = test_server.TestServer(port)
        server.count = 4
        server.start()
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        #url = stasis.buildUrl("localhost","user","pass","","http", port)
        url = "http://localhost:%s" % (port)
        status, out = commands.getstatusoutput("%s -u %s -U %s -P %s 32" % (
                                                self.script_name,
                                                url,
                                                self.username,
                                                self.password))
        self.assertEqual(status, 0)

    def test_report_local_pass(self):
        port = 8222
        server = test_server.TestServer(port)
        server.count = 4
        server.start()
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        url = stasis.buildUrl("localhost","user","pass","","http", port)
        xml_file = os.path.join("testopia_run_files","seq_report_pass.xml")
        params = {}
        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                                                self.sv,
                                                case_lib)
                

        sequence = sequence_lib.load(xml_file) 
        log_reporter = stasis.LogTestCaseReporter(2, logfile=log_file)
        sequence.addReporter(log_reporter)
        testopia_reporter = stasis.TestopiaCaseReporter(url)
        sequence.addReporter(testopia_reporter)
        runner = stasis.Runner(sequence, params)
        runner.run(wait_before_kill=3)
        begin_count = 0
        pass_count = 0
        total = 2
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search(" BEGIN ", line):
                begin_count += 1
            if re.search(" PASS ", line):
                pass_count += 1

        fd.close()
        self.assertEqual(pass_count, total)
        self.assertEqual(begin_count, total)

    def test_report_local_fail(self):
        port = 8232
        server = test_server.TestServer(port)
        server.count = 4
        server.start()
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        url = stasis.buildUrl("localhost","user","pass","","http", port)
        xml_file = os.path.join("testopia_run_files","seq_report_fail.xml")
        params = {}
        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                                                self.sv,
                                                case_lib)
                
        sequence = sequence_lib.load(xml_file) 
        log_reporter = stasis.LogTestCaseReporter(2, logfile=log_file)
        sequence.addReporter(log_reporter)
        testopia_reporter = stasis.TestopiaCaseReporter(url)
        sequence.addReporter(testopia_reporter)
        runner = stasis.Runner(sequence, params)
        runner.run(wait_before_kill=3)
        begin_count = 0
        pass_count = 0
        total = 2
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search(" BEGIN ", line):
                begin_count += 1
            if re.search(" ERROR ", line):
                pass_count += 1

        fd.close()
        self.assertEqual(pass_count, total)
        self.assertEqual(begin_count, total)

    def test_run_seqence_live(self):
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        if self.case_run_id is None:
            case_run_id = raw_input("case_run_id: ")
        else:
            case_run_id = self.case_run_id

        user = "timl33"
        if self.password is None:
            passwd = raw_input("Password for %s: " % user)
        else:
            passwd = self.passwd
        url = stasis.buildUrl("bugzillastage.provo.novell.com", user, passwd)
        params = {}
        sequence_lib = stasis.TestopiaSequenceLibrary(self.cv, 
                                                    case_lib,
                                                    url)
        sequence = sequence_lib.load(case_run_id) 
        log_reporter = stasis.LogTestCaseReporter(2, logfile=log_file)
        sequence.addReporter(log_reporter)
        runner = stasis.Runner(sequence, params)
        runner.run(wait_before_kill=3)
        begin_count = 0
        pass_count = 0
        total = 2
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search(" BEGIN ", line):
                begin_count += 1
            if re.search(" PASS ", line):
                pass_count += 1

        fd.close()
        self.assertEqual(pass_count, total)
        self.assertEqual(begin_count, total)
        
    def test_report_live(self):
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        #uri = os.path.join(os.getcwd(),"testopia")
        #hostname = "bugzillastage.provo.novell.com"
        #hostname = "localhost:%s" % self.port
        if self.case_run_id is None:
            case_run_id = raw_input("case_run_id: ")
        else:
            case_run_id = self.case_run_id

        if self.user is None:
            user = raw_input("Password for %s: " % user)
        else:
            user = self.passwd

        if self.password is None:
            passwd = raw_input("Password for %s: " % user)
        else:
            passwd = self.passwd
        #password = "password"
        url = stasis.buildUrl("bugzillastage.provo.novell.com", user, passwd)
        params = {}
        sequence_lib = stasis.TestopiaSequenceLibrary(self.cv, 
                                                    case_lib,
                                                    url)
        sequence = sequence_lib.load(case_run_id) 
        log_reporter = stasis.LogTestCaseReporter(2, logfile=log_file)
        sequence.addReporter(log_reporter)
        testopia_reporter = stasis.TestopiaCaseReporter(url)
        sequence.addReporter(testopia_reporter)
        runner = stasis.Runner(sequence, params)
        runner.run(wait_before_kill=3)
        begin_count = 0
        pass_count = 0
        total = 2
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search(" BEGIN ", line):
                begin_count += 1
            if re.search(" PASS ", line):
                pass_count += 1

        fd.close()
        self.assertEqual(pass_count, total)
        self.assertEqual(begin_count, total)

def main( args ):
    sys.path.append(os.path.realpath("."))
    base_name = os.path.splitext( os.path.basename(sys.argv[0]) )[0]
    usage = "usage: %prog -t TEST_CASE [-i case_run_id] [-p password]"
    parser = stasis.OptionParser( usage=usage )
    parser.add_option("-c", "--case_run_id", 
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
                       help="Port of server, script will not start a server", 
                       action="store" )
    parser.add_option("-S", "--server", 
                       default=None,
                       help="server", 
                       action="store" )
    parser.add_option("-t", "--test", 
                       dest="test_case_list", 
                       default=[],
                       help="Test case", 
                       metavar="TEST_CASE", 
                       action="append" )
    parser.add_option("-u", "--url", 
                       default=None,
                       help="Username", 
                       action="store" )
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
  
    TestScripts.password = options.password
    TestScripts.user = options.user
    TestScripts.url = options.url 
    TestScripts.case_run_id = options.case_run_id
    TestScripts.port = options.port
    TestScripts.server = options.server
    TestScripts.case_run_id = options.case_run_id

  
    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    suite = unittest.TestSuite()
    if len( options.test_case_list ) != 0:
        for test_case in options.test_case_list:
            suite.addTest( TestScripts( test_case ) )
    elif options.local:
        for test_case in TestScripts.local_cases:
            suite.addTest( TestScripts( test_case ) )
    else:
        suite = unittest.makeSuite( TestScripts )
            
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

