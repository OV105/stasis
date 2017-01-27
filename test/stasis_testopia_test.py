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

class TestStasisTestopia(unittest.TestCase):
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
        setup_environment.setup_files()
        self.env_old_path = setup_environment.setup_path()

    def tearDown(self):
        pass
        
    def test_run_sequence_live(self):
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        if self.case_run_id is None:
            case_run_id = raw_input("case_run_id: ")
        else:
            case_run_id = self.case_run_id

        if self.url is None:
            if self.user is None:
                user = raw_input("Enter testopia user name: ")
            else:
                user = self.user

            if self.password is None:
                passwd = raw_input("Password for %s: " % user)
            else:
                passwd = self.password

            if self.server is None:
                server = raw_input("Server: ")
            else:
                server = self.server
            url = stasis.buildUrl(server, user, passwd)
        else:
            url = self.url

        params = {}


        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(None, case_run_id) 
        log_reporter = stasis.LogTestCaseReporter(3, logfile=log_file)
        series.addReporter(log_reporter)
        dispatcher = stasis.RunDispatcher(series)
        dispatcher.run()
        
        begin_count = 0
        pass_count = 0
        total = 3
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
        if self.case_run_id is None:
            case_run_id = raw_input("case_run_id: ")
        else:
            case_run_id = self.case_run_id
            
        if self.url is None:
            if self.user is None:
                user = raw_input("Enter testopia user name: ")
            else:
                user = self.user

            if self.password is None:
                passwd = raw_input("Password for %s: " % user)
            else:
                passwd = self.password

            if self.server is None:
                server = raw_input("Server: ")
            else:
                server = self.server
            url = stasis.buildUrl(server, user, passwd)
        else:
            url = self.url
        params = {}


        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(None, case_run_id) 
        log_reporter = stasis.LogTestCaseReporter(3, logfile=log_file)
        series.addReporter(log_reporter)
        testopia_reporter = stasis.TestopiaCaseReporter(url)
        sequence.addReporter(testopia_reporter)
        dispatcher = stasis.RunDispatcher(series)
        dispatcher.run()
        
        begin_count = 0
        pass_count = 0
        total = 3
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
  
    TestStasisTestopia.password = options.password
    TestStasisTestopia.user = options.user
    TestStasisTestopia.url = options.url 
    TestStasisTestopia.case_run_id = options.case_run_id
    TestStasisTestopia.port = options.port
    TestStasisTestopia.server = options.server
    TestStasisTestopia.case_run_id = options.case_run_id
    TestStasisTestopia.debug = options.debug_level



    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    suite = unittest.TestSuite()
    if len( options.test_case_list ) != 0:
        for test_case in options.test_case_list:
            suite.addTest( TestStasisTestopia( test_case ) )
    else:
        suite = unittest.makeSuite( TestStasisTestopia )
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

