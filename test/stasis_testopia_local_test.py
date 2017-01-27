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
import threading
import ConfigParser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
xsd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),"stasis","xsd")
import stasis
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))
import test_server
import setup_environment

class TestStasisTestopiaLocal(unittest.TestCase):
    case_run_id = None
    user = None
    pasword = None
    server = None
    port = None
    debug = 3

    def setUp(self):
        self.old_path = sys.path
        self.cv = stasis.XMLValidator(os.path.join(xsd_dir, "test-case.xsd"))
        self.sv = stasis.XMLValidator(os.path.join(xsd_dir, "test-sequence.xsd"))
        self.rr = stasis.RoleRegistry()
        setup_environment.setup_files()
        self.env_old_path = setup_environment.setup_path()

    def tearDown(self):
        pass
        
    def test_run_seqence_local(self):
        if self.port is None:
            port = 8113
            count = 12
            server = test_server.TestServer(port, count)
            thread = threading.Thread(None, server.start_server)
            thread.start()
        else:
            port = self.port

        log_file = os.tempnam(None,"stasis-")
        print "Log file: %s" % (log_file)
        case_lib = stasis.TestCaseLibrary(self.cv)
        url = stasis.buildUrl("localhost","user","pass","/","http", port)
        params = {}
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(32, url) 
        
        log_reporter = stasis.LogTestCaseReporter(debug=TestStasisTestopiaLocal.debug, \
                                                  logfile=log_file)
        series.addReporter(log_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        case_pass_count = 0
        pass_count = 0
        total = 3
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search("CASE_PASS_", line):
                case_pass_count += 1
            if re.search(" PASS ", line):
                pass_count += 1

        fd.close()
        self.assertEqual(pass_count, total)
        self.assertEqual(case_pass_count, total)
       

    def test_sequence_save_ini(self):
        if self.port is None:
            port = 8817
            count = 12
            server = test_server.TestServer(port, count)
            thread = threading.Thread(None, server.start_server)
            thread.start()
        else:
            port = self.port

        ini_file = os.tempnam(None,"stasis_")
        case_lib = stasis.TestCaseLibrary(self.cv)
        url = stasis.buildUrl("localhost","user","pass","/","http", port)
        params = {}
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(32, url) 
        print "INI FILE: %s" % ini_file
        fd = open(ini_file, 'w')
        parser = ConfigParser.SafeConfigParser()
        for tc in series:
            tc.addConfSection(parser)

        parser.write(fd)
        fd.close()
        fd = open(ini_file, 'r')
        found_file_2 = False
        found_file_22 = False
        found_function = False
        line_count = 0
        section_count = 0
        lines = fd.readlines()
        fd.close()
        for line in lines:
            line_count += 1
            if re.search(' = case_pass_22', line):
                found_file_22 = True
            elif re.search(' = case_pass_2', line):
                found_file_2 = True
            elif re.search(' = test_case_pass_func', line):
                found_function = True
            elif re.search('\[.*/', line):
                section_count += 1
       
        self.assertEqual(line_count, 108)
        self.assertEqual(section_count, 9)
        self.assert_(found_file_2)
        self.assert_(found_file_22)
        self.assert_(found_function)

       
    def test_report_local_pass(self):
        if self.port is None:
            port = 8123
            count = 8
            server = test_server.TestServer(port, count)
            thread = threading.Thread(None, server.start_server)
            thread.start()
        else:
            port = self.port
        
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        url = stasis.buildUrl("localhost","user","pass","/","http", port)
        xml_file = "seq_report_pass.xml"
        params = {}
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(xml_file) 
        
        testopia_reporter = stasis.TestopiaCaseReporter(url)
        series.addReporter(testopia_reporter)
        log_reporter = stasis.LogTestCaseReporter(3, logfile=log_file)
        series.addReporter(log_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        
        case_pass_count = 0
        pass_count = 0
        total = 2
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search("CASE_PASS_", line):
                case_pass_count += 1
            if re.search(" PASS ", line):
                pass_count += 1

        fd.close()
        self.assertEqual(pass_count, total)
        self.assertEqual(case_pass_count, total)

    def test_report_local_fail(self):
        if self.port is None:
            port = 8133
            count = 8
            server = test_server.TestServer(port, count)
            thread = threading.Thread(None, server.start_server)
            thread.start()
        else:
            port = self.port

        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        url = stasis.buildUrl("localhost","user","pass","/","http", port)
        xml_file = "seq_report_fail.xml"
        params = {}
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(xml_file) 
        log_reporter = stasis.LogTestCaseReporter(3, logfile=log_file)
        series.addReporter(log_reporter)
        testopia_reporter = stasis.TestopiaCaseReporter(url)
        series.addReporter(testopia_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        case_fail_count = 0
        fail_count = 0
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search("CASE_FAIL_", line):
                case_fail_count += 1
            if re.search(" FAIL ", line):
                fail_count += 1

        fd.close()
        self.assertEqual(fail_count, 2)
        self.assertEqual(case_fail_count, 4)

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
                       default=3, 
                       help="Increase verbosity of debug output")

    (options,args) = parser.parse_args()
  
    TestStasisTestopiaLocal.password = options.password
    TestStasisTestopiaLocal.user = options.user
    TestStasisTestopiaLocal.url = options.url 
    TestStasisTestopiaLocal.case_run_id = options.case_run_id
    TestStasisTestopiaLocal.port = options.port
    TestStasisTestopiaLocal.server = options.server
    TestStasisTestopiaLocal.case_run_id = options.case_run_id
    TestStasisTestopiaLocal.debug = options.debug_level



    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    suite = unittest.TestSuite()
    if len( options.test_case_list ) != 0:
        for test_case in options.test_case_list:
            suite.addTest( TestStasisTestopiaLocal( test_case ) )
    else:
        suite = unittest.makeSuite( TestStasisTestopiaLocal )
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

