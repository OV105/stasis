
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

import sys
import os
import tempfile
import datetime
import pwd

GROUP = "Test case execution:"

def intro():
    return ["Run a local test case"]

def abbreviation():
    return "rtc"

def setOptions(parser, stasis):
    parser.set_usage("stasis run-test-case [options] <xml_file>|<module function>")
    parser.add_option("-A", "--arg",
                       action="append",
                       metavar="<var>=<value>",
                       dest="arg_list",
                       help="Variable and value to be passed to test run.")
    parser.add_option("-L", "--logdir", 
                      metavar="PATH",
                      help="Directory to place files from run in")
    parser.add_option("-s", "--suite",
                      dest="suite_list",
                      action="append",
                      metavar="FILE",
                      help="Suite to search for sequence file")
    parser.add_option("-y", "--cycle", 
                      type="int",
                      metavar="INT",
                      help="Number of times a test case is run.")
    
    parser.set_defaults(arg_list=[])
    parser.set_defaults(logdir=None)
    parser.set_defaults(suite_list=[])
    parser.set_defaults(cycle=1)

def runCommand(util):
    if len(util.args) < 2:
        sterr = "No xml file or, module and function provided"
        util.logger.critical(sterr)
        raise util.stasis.IncorrectArgument, sterr
    
    #if options.type not in stasis.RUN_TYPES:
    #    print "--type must be one of %s" % stasis.RUN_TYPES
    #    parser.print_usage()
    #    sys.exit(1)
    case_lib, sequence_lib = util.getStasisLibs()
    
    if len(util.args) == 2:
        tc = case_lib.load(util.args[1])
        util.logger.info("TestCase: %s" % tc.getName())
    elif len(util.args) == 3:
        tc = case_lib.load(util.args[1], util.args[2])
        util.logger.info("TestCase: %s" % tc.getName())
    else:
        sterr = "Incorrect number of arguments"
        util.logger.critical(sterr)
        raise util.stasis.IncorrectArgument, sterr
    
    series = util.stasis.TestSeries(tc.getName())
    series.append(tc)
    series.logdir = util.logdir
    util.setReporters(series)
   
    if util.options.test:
        result = tc.getProperty('filename')
        if result is None:
            result = tc.getName()
        
        result = "%s\n\n%s" % (result, tc.getSourceHandler().getCode())
    else:
        util.logger.info("logdir %s", util.logdir)
        if not os.path.isdir(util.logdir):
            os.mkdir(util.logdir)
       
        result = util.runSeries(series)

    return result
