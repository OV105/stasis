
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

GROUP = "TestSeries conf files"

def intro():
    return ["Run local conf/ini test series file"]

def abbreviation():
    return "rcf"

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
    parser.add_option("-R", "--role",
                      action="append", 
                      metavar="<role>=<address>",
                      dest="roles",
                      help="Specify a machine running staf.")
    parser.add_option("-s", "--suite",
                      dest="suite_list",
                      action="append",
                      metavar="FILE",
                      help="Suite to search for sequence file")
    parser.add_option("-S", "--status_filter", 
                      action="append",
                      dest="status_filters",
                      choices=stasis.STATUS_LIST,
                      help="Filter(s) for status of test cases: %s" % \
                                    (stasis.STATUS_LIST))
    parser.add_option("-y", "--cycle", 
                      type="int",
                      metavar="INT",
                      help="Number of times a test case is run.")
    
    parser.set_defaults(arg_list=[])
    parser.set_defaults(logdir=None)
    parser.set_defaults(roles=[])
    parser.set_defaults(suite_list=[])
    parser.set_defaults(status_filters=[])
    parser.set_defaults(cycle=1)

def runCommand(util):
    xsd_dir = os.path.join(os.path.dirname(stasis.__file__), "xsd")
    if len(parsed_args) < 1:
        sterr = "No test series conf file provided"
        logger.critical(sterr)
        raise stasis.IncorrectArgument, sterr
    
    if options.logdir is None:
        dir_name = "stasis-run-%s-%s" % (pwd.getpwuid(os.getuid())[0],
                                    datetime.datetime.now().
                                    strftime("%b-%d-%H%M"))
        logdir = os.path.join(tempfile.gettempdir(), dir_name)
    else:
        logdir = options.logdir
    
    logger.info("logdir %s", logdir)
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    
    case_lib, sequence_lib = stasis.getStasisLibs(xsd_dir, 
                                                  options.suite_list,
                                                  options.config_files)
    
    try:
        series = sequence_lib.load(parsed_args[1])
        series.logdir = logdir
    except stasis.XMLValidationError, e:
        sterr = "Failed to parse file: %s\n %s" % (seq_file, e)
        logger.error(sterr)
        raise e
                                            
    if options.test:
        result = series.textList()
    else:
        logger.info("logdir %s", logdir)
        if not os.path.isdir(logdir):
            os.mkdir(logdir)
       
        stasis.addReporters(series, logdir, options.verbose, options.console)
        result = stasis.runSeries(series, options.arg_list, options.cycle,\
                                  options.register, options.role)
    return result
    
