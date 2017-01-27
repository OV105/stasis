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
import ConfigParser
import popen2
import shutil
import getpass
import setup_environment

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
#sys.path.append(os.path.expanduser("~/stasis/unittest/unittest_module_files"))
xsd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),"stasis","xsd")
import stasis

class TestCase(unittest.TestCase):
    arg_dict = {}
    def setUp(self):
        self.old_path = sys.path
        self.cv = stasis.XMLValidator(os.path.join(xsd_dir, "test-case.xsd"))
        self.sv = stasis.XMLValidator(os.path.join(xsd_dir, "test-sequence.xsd"))
        self.rr = stasis.RoleRegistry()
        setup_environment.setup_files()

    def tearDown(self):
        pass

    def test_run_xml_case(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("case_pass_2.xml")
       
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr)
        run_dispatch.run()
       
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
       
        self.assertEqual( pass_count, 1 )

    def test_run_conf_arg_case(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("case_conf_arg.xml")
       
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr)
        run_dispatch.run()
       
        fd = open( log_file, 'r' )
        pass_count = 0
        conf_count = 0
        value_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
            elif re.search( "^CASE_CONF_ARG", line ):
                conf_count += 1
                if re.search( ": value [12]", line ):
                    value_count += 1
      
        self.assertEqual(tc.values['conf_arg_1'], "value 1")
        self.assertEqual(tc.values['conf_arg_2'], "value 2")
        self.assertEqual(tc.getProperty('suite_name'), "stasis_unittest")
        self.assertEqual(tc.getProperty('version'), '1')
        self.assertEqual(pass_count, 1)
        self.assertEqual(value_count, 2)
        self.assertEqual(conf_count, 3)

    def test_xml_shell_types(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("case_types_param_shell.xml")
       
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr, \
                         {"name":"string","count":5,"queue":['a','b','c']})
        run_dispatch.run()
       
        fd = open( log_file, 'r' )
        pass_count = 0
        fail_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( "PASS TYPE ", line ):
                pass_count += 1
                continue
            if re.search( "FAIL TYPE ", line ):
                fail_count += 1
                continue
       
        self.assertEqual(pass_count, 3)
        self.assertEqual(fail_count, 0)

    def test_xml_python_types(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("case_types_param_python.xml")
       
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr, \
                         {"name":"string","count":5,"queue":['a','b','c']})
        run_dispatch.run()
       
        fd = open( log_file, 'r' )
        pass_count = 0
        fail_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( "PASS TYPE ", line ):
                pass_count += 1
                continue
            if re.search( "FAIL TYPE ", line ):
                fail_count += 1
                continue
       
        self.assertEqual(pass_count, 3)
        self.assertEqual(fail_count, 0)

    def test_run_ls_file(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
       
        case_lib = stasis.TestCaseLibrary(self.cv, "stasis_examples")
        tc = case_lib.load("ls_file_shell.xml")
        
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr, {"filename":"/tmp"})
        run_dispatch.run()
       
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
       
        self.assertEqual( pass_count, 1 )

    def test_run_try_ping_func(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
       
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("ping_test_func", "try_ping")
        
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr, {"host":"localhost"})
        run_dispatch.run()
       
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
       
        self.assertEqual( pass_count, 1 )

    def test_run_ping_python_default(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv, "stasis_examples")
        tc = case_lib.load("ping_python.xml")
        
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr)
        run_dispatch.run()
       
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
       
        self.assertEqual( pass_count, 1 )

    def test_xml_case_load_ini(self):
        def md5sum(file):
            import md5
            fd = open(file)
            digest = md5.new()
            buffer = fd.read(4096)
            while buffer != "":
                digest.update(buffer)
                buffer = fd.read(4096)
            
            fd.close()
            return digest.hexdigest()

        ini_file = os.tempnam(None,"stasis_")
        print "INI FILE: %s" % ini_file
        file_name = "case_pass_2.xml"
       
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load(file_name)
        name = tc.getName()
        tc.values = {'key1':'value1','key2':'value2','key3':'value3'}
        tc.substitutions = {'dest1':'rule1','dest2':'rule2','dest3':'rule3'}
        fd = open(ini_file, 'w')
        parser = ConfigParser.SafeConfigParser()
        tc.addConfSection(parser)
        parser.write(fd)
        fd.close()
        del(parser)

        tc1 = stasis.TestCase(stasis.EmptySourceHandler(), "Empty")
        parser = ConfigParser.SafeConfigParser()
        fd = open(ini_file, 'r')
        parser.readfp(fd)
        fd.close()
        tc1.loadConf(parser)
        del(parser)
        parser = ConfigParser.SafeConfigParser()
        tc1.addConfSection(parser)
        resave = "%s.resave" % (ini_file)
        fd = open(resave, 'w')
        parser.write(fd)
        fd.close()
        
        original = md5sum(ini_file)
        resave = md5sum(resave)
        self.assertEqual(original, resave)

    def test_xml_case_save_ini(self):
        ini_file = os.tempnam(None,"stasis_")
        print "INI FILE: %s" % ini_file
        file_name = "case_pass_2.xml"
       
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load(file_name)
        tc.values = {'key1':'value1','key2':'value2','key3':'value3'}
        tc.substitutions = {'dest1':'rule1','dest2':'rule2','dest3':'rule3'}
        fd = open(ini_file, 'w')
        parser = ConfigParser.SafeConfigParser()
        tc.addConfSection(parser)
        parser.write(fd)
        fd.close()
        fd = open(ini_file, 'r')
        line_count = 0
        #found_file = False
        rule_count = 0
        value_count = 0
        section_count = 0
        lines = fd.readlines()
        fd.close()
        for line in lines:
            line_count += 1
            #if re.search("= %s" % (file_name), line):
            #    found_file = True
            if re.search('value[1,2,3]{1}', line):
                value_count += 1
            elif re.search('rule[1,2,3]{1}', line):
                rule_count += 1
            elif re.search('\[.*/', line):
                section_count += 1
       
        self.assertEqual(line_count, 42)
        self.assertEqual(rule_count, 3)
        self.assertEqual(value_count, 3)
        self.assertEqual(section_count, 4)
        #self.assert_(found_file)

    def test_xml_case_load_ini(self):
        ini_file = os.tempnam(None,"stasis_")
        print "INI FILE: %s" % ini_file
        file_name = "case_pass_2.xml"
       
        #case_lib = stasis.TestCaseLibrary(self.cv)
        #tc = case_lib.load(file_name)
        #tc.substitutions = {'dest1':'rule1','dest2':'rule2','dest3':'rule3'}
        tc = stasis.TestCase(stasis.EmptySourceHandler(\
                         'stasis_unittest+case_pass_2.xml'))
        parser = ConfigParser.SafeConfigParser()
        parser.readfp(open(os.path.expanduser(os.path.expanduser(\
                 '~/stasis/unittest/unittest_ini_files/load_ini_case.ini'))))
        tc.loadConf(parser)

        self.assertEqual(tc.getProperty('status'), 'NOTRUN')
        self.assertEqual(tc.getProperty('filename'), 'case_pass_2.xml')
        self.assertEqual(tc.getProperty('blocks-all'), None)
        self.assertEqual(len(tc.values), 3)
        self.assertEqual(len(tc.substitutions), 3)
        tc.values = {'key1':'value1','key2':'value2','key3':'value3'}
        fd = open(ini_file, 'w')
        parser = ConfigParser.SafeConfigParser()
        tc.addConfSection(parser)
        parser.write(fd)
        fd.close()
        fd = open(ini_file, 'r')
        line_count = 0
        found_file = False
        rule_count = 0
        value_count = 0
        section_count = 0
        lines = fd.readlines()
        fd.close()
        for line in lines:
            line_count += 1
            #if re.search("= %s" % (file_name), line):
            #    found_file = True
            if re.search('value[1,2,3]{1}', line):
                value_count += 1
            elif re.search('rule[1,2,3]{1}', line):
                rule_count += 1
            elif re.search('\[.*/', line):
                section_count += 1
       
        self.assertEqual(line_count, 42)
        self.assertEqual(rule_count, 3)
        self.assertEqual(value_count, 3)
        self.assertEqual(section_count, 4)
        #self.assert_(found_file)

    def test_run_module_case(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        #tc = case_lib.loadFromModule("stasis_unittest", "test_case_pass_func")
        tc = case_lib.load("stasis_unittest", "test_case_pass_func")
        #runner = stasis.Runner(tc, {})
        #run_seq = stasis.RunSequence([runner])
        #sequence = stasis.TestSequence(tc.getName(), '', run_seq, 
#                                       tc.getParamList())
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr)
        #runner = stasis.Runner(sequence, {})
        #runner.run()
        run_dispatch.run()
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
       
        self.assertEqual( pass_count, 1 )
        
    def test_run_case_setup_teardown(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("case_setup_teardown.xml")
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)

        run_dispatch = stasis.RunDispatcher(series, self.rr,\
                {"archive_file_name":"case_archive_setup.tar.gz"}, timeout=60)
        run_dispatch.run()
        
        fd = open( log_file, 'r' )
        found_count = 0
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
            elif re.search("^found ", line):
                found_count += 1
       
        self.assertEqual(pass_count, 1)
        self.assertEqual(found_count, 3)

    def test_run_python_archive_case(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv, "stasis_examples")
        tc = case_lib.load("test_case_setup_python.xml")
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)

        run_dispatch = stasis.RunDispatcher(series, self.rr, \
                   {"archive_file_name":"archive_setup.tar.gz"}, timeout=60)
        run_dispatch.run()
        
        fd = open( log_file, 'r' )
        found_count = 0
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
            elif re.search("^found ", line):
                found_count += 1
       
        self.assertEqual(pass_count, 1)
        self.assertEqual(found_count, 3)

    def test_run_module_archive_case(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("stasis_unittest", "test_case_func_archive")
        
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=3, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr, \
         {"archive_file_name":"stasis_unittest+test_case_func_archive.tar.bz2"},\
         timeout=60)
        run_dispatch.run() 
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
       
        self.assertEqual( pass_count, 1 )

    def test_run_xml_param(self):
        log_file = os.tempnam(None,"stasis_")
        print "LOG FILE: %s" % log_file
        case_lib = stasis.TestCaseLibrary(self.cv)
        tc = case_lib.load("case_pass_param_2.xml")
        
        series = stasis.TestSeries(tc.getName())
        series.append(tc)
        log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        console_reporter = stasis.ConsoleTestCaseReporter()
        
        series.addReporter(log_reporter)
        series.addReporter(console_reporter)
        run_dispatch = stasis.RunDispatcher(series, self.rr, \
                        {"string_2":"two", "int_2":"2"})
        run_dispatch.run()

        
        #runner = stasis.Runner(tc, {})
        #run_seq = stasis.RunSequence([runner])
        #sequence = stasis.TestSequence(tc.getName(), '', run_seq, 
        #                               tc.getParamList())
        #log_reporter = stasis.LogTestCaseReporter(debug=2, logfile=log_file)
        #console_reporter = stasis.ConsoleTestCaseReporter()
        
        #sequence.addReporter(log_reporter)
        #sequence.addReporter(console_reporter)
        #runner = stasis.Runner(sequence, {"string_2":"two", "int_2":"2"})
        #runner.run()
        
        
        fd = open( log_file, 'r' )
        pass_count = 0
        lines = fd.readlines()
        for line in lines:
            if re.search( " PASS ", line ):
                pass_count += 1
                continue
       
        self.assertEqual( pass_count, 1 )


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

    TestCase.arg_dict = {}
    for arg in options.arg_list:
        split_arg = arg.split("=")
        TestStasis.arg_dict[split_arg[0]] = split_arg[1]
    
    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    if len( options.test_case_list ) == 0:
        suite = unittest.makeSuite( TestCase )
    else:
        suite = unittest.TestSuite()
        for test_case in options.test_case_list:
            suite.addTest( TestCase( test_case ) )
        
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

