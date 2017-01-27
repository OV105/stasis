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
import cPickle
import tempfile
import commands

STASIS_BASE = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
STASIS_SCRIPT_DIR = os.path.join(STASIS_BASE, "scripts")
STASIS_CMD = os.path.join(STASIS_SCRIPT_DIR, "stasis")
sys.path.append(STASIS_BASE)
xsd_dir = os.path.join(STASIS_BASE, "stasis","xsd")
PATH = "%s:%s" % (os.environ['PATH'],os.path.join(STASIS_BASE, "scripts"))
os.environ['PATH'] = PATH
import stasis
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))
import test_server
import setup_environment

import staf

class TestStasisStaf(unittest.TestCase):
    case_run_id = None
    user = None
    pasword = None
    server = None
    port = None
    debug = 3
    stafproc_cmd = "PATH=%s stafproc" % PATH

    def setUp(self):
        self.old_path = sys.path
        self.cv = stasis.XMLValidator(os.path.join(xsd_dir, "test-case.xsd"))
        self.sv = stasis.XMLValidator(os.path.join(xsd_dir, "test-sequence.xsd"))
        setup_environment.setup_files()
        self.env_old_path = setup_environment.setup_path()
        self.case_lib = stasis.TestCaseLibrary(self.cv)

    def tearDown(self):
        pass
        
    def test_pickle(self):
        tc1 = self.case_lib.load("case_pass_2.xml")
        pickle_file = os.tempnam(None, "pick-")
        fd = open(pickle_file, 'w')
        cPickle.dump(tc1, fd)
        fd.close()

        fd = open(pickle_file, 'r')
        tc2 = cPickle.load(fd)
        fd.close()
      
        self.assertEqual(tc1.getName(), tc2.getName())

    def test_run_pickle(self):
        tc1 = self.case_lib.load("case_pass_2.xml")
        pickle_file = os.tempnam(None, "pick-")
        fd = open(pickle_file, 'w')
        cPickle.dump(tc1, fd)
        fd.close()

        fd = open(pickle_file, 'r')
        tc2 = cPickle.load(fd)
        fd.close()
        self.assertEqual(tc1.getName(), tc2.getName())
        tc2.run({}, 5)
        self.assertEqual(tc2.getStatus(), stasis.STATUS_PASS)

    def test_staf_copy_tc(self):
        out = os.popen(self.stafproc_cmd)
        time.sleep(2)
        staf_handle = staf.STAFHandle("test_copy_tc")
        tmp_dir = os.tempnam(None, "pckl-")
        os.makedirs(tmp_dir)
        tc1 = self.case_lib.load("case_pass_2.xml")
        (pickle_fd, pickle_file) = tempfile.mkstemp(".pckl")
        os.close(pickle_fd)
        pckl_file_name = os.path.basename(pickle_file)
        pickle_fd = open(pickle_file, 'w')
        cPickle.dump(tc1, pickle_fd)
        pickle_fd.close()
        result1 = staf_handle.submit('local', "FS", \
                 'COPY FILE %s TODIRECTORY %s TOMACHINE local' % \
                 (pickle_file, tmp_dir)
                 )

        self.assertEqual(result1.rc, staf.STAFResult.Ok)

        result2 = staf_handle.submit('local', "PROCESS", \
              'START SHELL COMMAND "echo HI > %s" WAIT 6000 RETURNFILE %s' %\
              (os.path.join(tmp_dir, "echo.txt"), \
              os.path.join(tmp_dir, pckl_file_name)))

        un = staf.unmarshall(result2.result)
        tc2 = cPickle.loads(un.getRootObject()['fileList'][0]['data'])
        self.assertEqual(tc1.getName(), tc2.getName())
        result = staf_handle.submit('local', "shutdown", "shutdown")
        time.sleep(2)
        os.unlink(pickle_file)
        os.unlink(os.path.join(tmp_dir, "echo.txt"))
        os.unlink(os.path.join(tmp_dir, pckl_file_name))
        os.rmdir(tmp_dir)

    def test_run_tc_local(self):
        out = os.popen(self.stafproc_cmd)
        time.sleep(2)
        staf_handle = staf.STAFHandle("test_copy_tc")
        tmp_dir = os.tempnam(None, "pckl-")
        os.makedirs(tmp_dir)
        tc1 = self.case_lib.load("case_pass_2.xml")
        (pickle_fd, pickle_file) = tempfile.mkstemp(".pckl")
        os.close(pickle_fd)
        pckl_file_name = os.path.basename(pickle_file)
        pickle_fd = open(pickle_file, 'w')
        cPickle.dump(tc1, pickle_fd)
        pickle_fd.close()
        result1 = staf_handle.submit('local', "FS", \
                 'COPY FILE %s TODIRECTORY %s TOMACHINE local' % \
                 (pickle_file, tmp_dir)
                 )

        self.assertEqual(result1.rc, staf.STAFResult.Ok)

        result2 = staf_handle.submit('local', "PROCESS", \
              'START SHELL COMMAND "%s rpt %s" WAIT 6000 RETURNFILE %s' %\
              (STASIS_CMD, os.path.join(tmp_dir, pckl_file_name), \
              os.path.join(tmp_dir, pckl_file_name)))

        #import pdb;pdb.set_trace()

        un = staf.unmarshall(result2.result)
        tc2 = cPickle.loads(un.getRootObject()['fileList'][0]['data'])
        self.assertEqual(tc1.getName(), tc2.getName())
        self.assertEqual(tc2.getStatus(), stasis.STATUS_PASS)
        result = staf_handle.submit('local', "shutdown", "shutdown")
        time.sleep(2)
        os.unlink(pickle_file)
        os.unlink(os.path.join(tmp_dir, pckl_file_name))
        os.rmdir(tmp_dir)
       

    def test_run_tc_local(self):
        staf_out = os.popen(self.stafproc_cmd)
        time.sleep(2)
        staf_handle = staf.STAFHandle("test_copy_tc")
        cmd = "%s rtc -vv -r test -R test=local case_pass_2.xml" % (STASIS_CMD)
        cmd_out = os.popen(cmd)
        lines = cmd_out.read()
        status = cmd_out.close()
        self.assertEqual(status, None)
        pass_count = 0
        reg_expr = re.compile("PASS")
        for line in lines.split("\n"):
            if reg_expr.search(line):
                pass_count += 1
        
        self.assertEqual(pass_count, 1)
        result = staf_handle.submit('local', "shutdown", "shutdown")
        time.sleep(2)
        lines = staf_out.read()
        status = staf_out.close()

def main( args ):
    sys.path.append(os.path.realpath("."))
    base_name = os.path.splitext( os.path.basename(sys.argv[0]) )[0]
    usage = "usage: %prog -t TEST_CASE [-i case_run_id] [-p password]"
    parser = stasis.OptionParser( usage=usage )
    parser.add_option("-H", "--host", 
                       default="LOCAL",
                       help="server", 
                       action="store" )
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
                       default=3, 
                       help="Increase verbosity of debug output")

    (options,args) = parser.parse_args()
  
    runner = unittest.TextTestRunner( sys.stdout, verbosity=2 )
    suite = unittest.TestSuite()
    if len( options.test_case_list ) != 0:
        for test_case in options.test_case_list:
            suite.addTest(TestStasisStaf(test_case))
    else:
        suite = unittest.makeSuite(TestStasisStaf)
    runner.run( suite )

if __name__ == '__main__':
    main( sys.argv[1:] )

