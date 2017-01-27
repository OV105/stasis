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
    arg_dict = {}
    def setUp(self):
        self.old_path = sys.path
        self.cv = stasis.XMLValidator(os.path.join(xsd_dir, "test-case.xsd"))
        self.sv = stasis.XMLValidator(os.path.join(xsd_dir, "test-sequence.xsd"))
        self.rr = stasis.RoleRegistry()
        setup_environment.setup_files()

    def tearDown(self):
        pass

    def test_run_sequence(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_all.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
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
        self.assertEqual( fail_count, 2 )

    def test_run_example_sequence(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("example_sequence.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                
        self.assertEqual( pass_count, 4 )

    def test_load_ini_sequence(self):
        ini_file = os.tempnam(None,"stasis_")
        print "INI FILE: %s" % ini_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("load_ini_sequence.ini")
        console_reporter = stasis.ConsoleTestCaseReporter()
        series.addReporter(console_reporter)
        fd = open( ini_file, 'w' )
        parser = ConfigParser.SafeConfigParser()
        for tc in series:
            tc.addConfSection(parser)

        parser.write(fd)
        fd.close()
        sect_count = 0
        pass_count = 0
        fail_count = 0
        fd = open( ini_file, 'r' )
        lines = fd.readlines()
        fd.close()
        for line in lines:
            if re.search( "\+case_.*./default\]", line ):
                sect_count += 1
                continue
                
            if re.search( "^status = FAIL", line ):
                fail_count += 1
       
            if re.search( "^status = PASS", line ):
                pass_count += 1
       
        self.assertEqual(sect_count, 4)
        #self.assertEqual(archive_count, 4)
        self.assertEqual(pass_count, 2)
        self.assertEqual(fail_count, 2)

    def test_save_ini_sequence(self):
        ini_file = os.tempnam(None,"stasis_")
        print "INI FILE: %s" % ini_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_all.xml")
        console_reporter = stasis.ConsoleTestCaseReporter()
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        fd = open( ini_file, 'w' )
        parser = ConfigParser.SafeConfigParser()
        for tc in series:
            tc.addConfSection(parser)

        parser.write(fd)
        fd.close()
        sect_count = 0
        #archive_count = 0
        fail_count = 0
        pass_count = 0
        fd = open( ini_file, 'r' )
        lines = fd.readlines()
        fd.close()
        for line in lines:
            if re.search( "\+case_.*./default\]", line ):
                sect_count += 1
                continue
                
            if re.search( "^status = FAIL", line ):
                fail_count += 1
       
            if re.search( "^status = PASS", line ):
                pass_count += 1
       
        self.assertEqual( sect_count, 4 )
        self.assertEqual(pass_count, 2)
        self.assertEqual(fail_count, 2)
        #self.assertEqual( archive_count, 4 )

    def test_print_ini_sequence(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_all.xml")
        series.printConf()
    
    def test_seq_subst_run_arg(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)


        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_subst_run_arg.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
        self.assertEqual( pass_count, 2 )

    def test_seq_arg_run_subst(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)


        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_arg_run_subst.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
        self.assertEqual( pass_count, 2 )

    def test_seq_subst_arg(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)

        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_subst_arg.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
        self.assertEqual( pass_count, 2 )

    def test_seq_arg(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)


        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_run_arg.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
        self.assertEqual( pass_count, 2 )

    def test_seq_run_arg(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)


        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        series = sequence_lib.load("seq_run_arg.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()

        
        #sequence_lib = stasis.TestSequenceLibrary(self.cv,
        #                                          self.sv,
        #                                          case_lib)
        
        #sequence = sequence_lib.load("seq_param_arg.xml")
        #log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        #console_reporter = stasis.ConsoleTestCaseReporter()
        #sequence.addReporter(log_reporter)
        #sequence.addReporter(console_reporter)
        #register_roles()
        #runner = stasis.Runner(sequence, {})
        #runner.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
        self.assertEqual( pass_count, 2 )

    def test_run_seq_pass_param(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        
        series = sequence_lib.load("seq_param_pass.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        series.addReporter(log_reporter)
        console_reporter = stasis.ConsoleTestCaseReporter()
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr, {"string_2":"two",\
                        "string_22":"twotwo", "int_2":"2", "int_22":"22"})
        dispatcher.run()
        #dispatcher.run({"string_2":"two",
                        #"string_22":"twotwo",
                        #"int_2":"2",
                        #"int_22":"22"})
        #runner = stasis.Runner(sequence, {"string_2":"two",
         #                                 "string_22":"twotwo",
          #                                "int_2":"2",
        #                                  "int_22":"22"})
        #runner.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
                
        self.assertEqual( pass_count, 2 )

    def test_run_seq_pass_param_fail(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        
        #value = {"string_2":"two", "string_22":"twotwo", "int_22":"22"}
        series = sequence_lib.load("seq_param_pass.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        dispatcher = stasis.RunDispatcher(series, self.rr)
        dispatcher.run()
        
        fd = open( log_file, 'r' )
        fail_count = 0
        missing_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search(" FAIL ", line ):
                fail_count += 1
            elif re.search(" missing parameter: ", line):
                missing_count += 1
                
        self.assertEqual(fail_count, 2)
        self.assertEqual(missing_count, 2)
        #sequence.addReporter(console_reporter)
        #register_roles()
        #runner = stasis.Runner(sequence, {"string_2":"two",
        #                                  "string_22":"twotwo",
        #                                  "int_22":"22"})
        #self.assertRaises(stasis.MissingParameter, runner.run)

    def test_run_seq_fail_param(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        sequence_lib = stasis.TestSequenceLibrary(case_lib)
        
        series = sequence_lib.load("seq_param_fail.xml")
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        #register_roles()
        dispatcher = stasis.RunDispatcher(series, self.rr, {"string_2":"two",\
                        "int_2":"2"})
        dispatcher.run()
        #dispatcher.run({"string_2":"two",
        #                "int_2":"2"})
        #runner = stasis.Runner(sequence, {"string_2":"two",
        #                                  "int_2":"2"})
        #runner.run()
        fd = open( log_file, 'r' )
        fail_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " FAIL ", line ):
                fail_count += 1
                continue
                
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
                       default=0, 
                       help="Increase verbosity of debug output")
    (options,args) = parser.parse_args()

    TestSequence.arg_dict = {}
    for arg in options.arg_list:
        split_arg = arg.split("=")
        TestStasis.arg_dict[split_arg[0]] = split_arg[1]
    
    #logger = logging.getLogger( "pyxt_pyxt_test" )
    #logger.setLevel( 30 - options.debug_level * 10 )
    #if options.log_file is None:
    #    handler = logging.StreamHandler()
    #else:
    #    handler = logging.FileHandler( options.log_file, 'w' )

    #formatter = logging.Formatter( "\n%(name)s(), %(threadName)s [%(created)f] - %(filename)s:%(lineno)s\n %(message)s" )
    #handler.setFormatter( formatter )
    #logger.addHandler( handler )

    #TestPyxt.logger = logger
    #TestPyxt.debug_level = options.debug_level
    
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

