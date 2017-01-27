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
import setup_environment

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
xsd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),"stasis","xsd")
import stasis

class TestStasis(unittest.TestCase):
    arg_dict = {}
    def setUp(self):
        self.old_path = sys.path
        self.cv = stasis.XMLValidator(os.path.join(xsd_dir, "test-case.xsd"))
        self.sv = stasis.XMLValidator(os.path.join(xsd_dir, "test-sequence.xsd"))
        setup_environment.setup_files()

    def tearDown(self):
        sys.path = self.old_path

    def test_conf_default(self):
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                                                    self.sv,
                                                    case_lib)
        #sequence_lib.load( "seq_1.xml" ) 
        sequence_lib.load( "seq_all.xml" ) 
        suites = sequence_lib.getSuiteNames()
        self.assertEqual(suites.count("stasis_unittest"), 1)
        self.assertEqual(suites.count("live_integration"), 1)
        paths = sequence_lib.getPaths()
        self.assertEqual(paths.count("/tmp"), 1)
        self.assertEqual(paths.count("/var/tmp"), 1)
        self.assertEqual(paths.count("/usr/tmp"), 1)
        self.assertEqual(paths.count(os.getcwd()), 1)
        self.assertEqual(paths.count(os.path.expanduser("~/stasis/test_run_files")), 1)
        xml_files = sequence_lib.list()
        for file in ["case_1_1a.xml","case_1_1b.xml","case_1_2a.xml",
                     "case_1a.xml","seq_1.xml","seq_1_2.xml"]:
            self.assertEqual(xml_files.count(file), 1)

    def test_add_path(self):
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                                                    self.sv,
                                                    case_lib)
        suites = sequence_lib.getSuiteNames()
        self.assertEqual(suites.count("unittest_default_2_sect"), 1)
        self.assertEqual(suites.count("unittest_default_1_sect"), 1)
        sequence_lib.addPath(os.path.expanduser("~/stasis/unittest/add_path"))
        sequence = sequence_lib.load( "seq_add_path_1.xml" ) 
        paths = sequence_lib.getPaths()
        self.assertEqual(paths.count(os.path.expanduser("~/stasis/unittest/add_path")), 1)
        xml_files = sequence_lib.list()
        self.assert_(xml_files.count("seq_add_path_1.xml"), 1)
        self.assert_(xml_files.count("case_add_path_1a.xml"), 1)
        

    def test_add_conf(self):
        def sub_test_add_conf(sequence_lib):
            suites = sequence_lib.getSuiteNames()
            self.assertEqual(suites.count("unittest_add_path_sect"), 1)
            self.assertEqual(suites.count("unittest_default_1_sect"), 1)
            sequence = sequence_lib.load( "seq_add_path_1.xml" ) 
            paths = sequence_lib.getPaths()
            self.assertEqual(paths.count(os.path.expanduser("~/stasis/unittest/add_path")), 1)
            self.assertEqual(paths.count(os.path.expanduser("~/stasis/unittest")), 1)
            xml_files = sequence_lib.list()
            self.assert_(xml_files.count("case_add_path_1a.xml"), 1)
            self.assert_(xml_files.count("seq_add_path_1.xml"), 1)

        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                                                    self.sv,
                                                    case_lib)
        sequence_lib.addConfFile(os.path.expanduser("~/stasis/unittest/add_path.conf"))
        sub_test_add_conf(sequence_lib)
        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                            self.sv,
                            case_lib,
                            os.path.expanduser("~/stasis/unittest/add_path.conf"))
        sub_test_add_conf(sequence_lib)
        
    def test_run_seqence_default(self):
        log_file = os.tempnam(None,"stasis-")
        case_lib = stasis.TestCaseLibrary(self.cv)
        params = {"zlmserver":"zlmserver.novell.com",
                  "key":"my_key",
                  "var_zlmserver":"var_zlmserver.novell.com"}
        for key in self.arg_dict.iterkeys():
            params[key] = self.arg_dict[key]

        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                                                    self.sv,
                                                    case_lib)
        sequence = sequence_lib.load( "seq_1.xml" ) 
        #sequence = sequence_lib.load( "seq_1_2.xml" ) 
        log_reporter = stasis.LogTestCaseReporter(3, logfile=log_file)
        sequence.addReporter(log_reporter)
        runner = stasis.Runner(sequence, params)
        runner.run(wait_before_kill=3)
        begin_count = 0
        pass_count = 0
        total = 5
        fd = open(log_file, 'r')
        for line in fd.readlines():
            if re.search(" BEGIN ", line):
                begin_count += 1
            if re.search(" PASS ", line):
                pass_count += 1
        fd.close()
        self.assertEqual(pass_count, total)
        self.assertEqual(begin_count, total)
        
    def test_run_seqence_add_path(self):
        log_file = os.tempnam(None,"stasis_")
        case_lib = stasis.TestCaseLibrary(self.cv)
        params = {"zlmserver":"zlmserver.novell.com",
                  "key":"my_key",
                  "var_zlmserver":"var_zlmserver.novell.com"}
        for key in self.arg_dict.iterkeys():
            params[key] = self.arg_dict[key]

        sequence_lib = stasis.TestSequenceLibrary(self.cv, 
                                                    self.sv,
                                                    case_lib)
        sequence_lib.addConfFile(os.path.expanduser("~/stasis/unittest/add_path.conf"))
        sequence = sequence_lib.load( "seq_add_path_1.xml" ) 
        log_reporter = stasis.LogTestCaseReporter(3, logfile=log_file)
        sequence.addReporter(log_reporter)
        runner = stasis.Runner(sequence, params)
        runner.run(wait_before_kill=3)
        begin_count = 0
        pass_count = 0
        total = 10
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
    sys.path.append( os.path.realpath( "." ) )
    base_name = os.path.splitext( os.path.basename(sys.argv[0]) )[0]
    usage = "usage: %prog -t TEST_CASE"
    parser = stasis.OptionParser( usage=usage )
    parser.add_option("-A", "--arg",
                       action="append",
                       dest="arg_list",
                       default=[],
                       metavar="<var>=<value>",
                       help="Variable and value to be passed to test run")
    parser.add_option("-t", "--test", 
                       dest="test_case_list", 
                       default=[],
                       help="Test case", 
                       metavar="TEST_CASE", 
                       action="append" )
    parser.add_option("-v", "--verbose", 
                       action="count", 
                       dest="debug_level", 
                       default=0, 
                       help="Increase verbosity of debug output")
    (options,args) = parser.parse_args()

    TestStasis.arg_dict = {}
    for arg in options.arg_list:
        split_arg = arg.split("=")
        TestStasis.arg_dict[split_arg[0]] = split_arg[1]
    
    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    if len( options.test_case_list ) == 0:
        suite = unittest.makeSuite( TestStasis )
    else:
        suite = unittest.TestSuite()
        for test_case in options.test_case_list:
            suite.addTest( TestStasis( test_case ) )
        
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

