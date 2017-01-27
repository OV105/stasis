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
import ConfigParser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
xsd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),"stasis","xsd")
import stasis

class TestSequence(unittest.TestCase):
    debug=2
    arg_dict = {}
    def setUp(self):
        self.old_path = sys.path
        self.cv = stasis.XMLValidator(os.path.join(xsd_dir, "test-case.xsd"))
        self.sv = stasis.XMLValidator(os.path.join(xsd_dir, "test-sequence.xsd"))
        setup_environment.setup_files()

    def tearDown(self):
        pass

    def test_block_all(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(None, "seq_block_all.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=TestSequence.debug,\
                                                  logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        blocked_count = 0
        failed_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search(" PASS ", line):
                pass_count += 1
                continue
            elif re.search(" BLOCKED ", line):
                blocked_count += 1
            elif re.search(" FAIL ", line):
                failed_count += 1
                
        self.assertEqual(pass_count, 0)
        self.assertEqual(blocked_count, 5)
        self.assertEqual(failed_count, 1)
        
    def test_run_back_fore(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(None, "seq_back_fore.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=TestSequence.debug,\
                                                  logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search(" PASS ", line):
                pass_count += 1
                continue
                
        self.assertEqual(pass_count, 3)

    def test_run_4deep_sequence(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(None, "seq_4deep_1.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=TestSequence.debug, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
       
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        fail_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
            if re.search( " FAIL ", line ):
                fail_count += 1
       
        self.assertEqual( pass_count, 4 )
        self.assertEqual( fail_count, 0 )

    def test_run_example_sequence(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(None, "example_sequence.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=TestSequence.debug,\
                                                  logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        fail_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
            if re.search( " FAIL ", line ):
                fail_count += 1
       
        self.assertEqual( pass_count, 3 )
        self.assertEqual( fail_count, 0 )

    def test_run_collective(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load(None, "seq_collective.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=TestSequence.debug, \
                                                  logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        fail_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
            if re.search( " FAIL ", line ):
                fail_count += 1
       
        self.assertEqual( pass_count, 2 )
        self.assertEqual( fail_count, 1 )

def main( args ):
    sys.path.append( os.path.realpath( "." ) )
    base_name = os.path.splitext( os.path.basename(sys.argv[0]) )[0]
    usage = "usage: %prog -t TEST_CASE"
    parser = stasis.OptionParser( usage=usage )
    #parser.add_option("-f", "--file", dest="log_file", default=None,
    #                   help="Log file", metavar="/PATH/FILE", action="store" )
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
                       default=2, 
                       help="Increase verbosity of debug output")
    (options,args) = parser.parse_args()

    TestSequence.arg_dict = {}
    for arg in options.arg_list:
        split_arg = arg.split("=")
        TestStasis.arg_dict[split_arg[0]] = split_arg[1]
    
    TestSequence.debug = options.debug_level
    
    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    if len( options.test_case_list ) == 0:
        suite = unittest.makeSuite( TestSequence )
    else:
        suite = unittest.TestSuite()
        for test_case in options.test_case_list:
            suite.addTest( TestSequence( test_case ) )
        
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

