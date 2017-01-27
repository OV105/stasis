
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
    return ["Run a local test sequence"]

def abbreviation():
    return "rts"

def setOptions(parser, stasis):
    parser.set_usage("stasis run-test-case [options] <sequence xml file>")
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
    stasis = util.stasis
    if len(util.args) < 2:
        sterr = "No sequence xml file"
        util.logger.critical(sterr)
        raise stasis.IncorrectArgument, sterr
    
    if not os.path.isdir(util.logdir):
        util.logger.info("Creating logdir %s", util.logdir)
        os.mkdir(util.logdir)
    
    case_lib, sequence_lib = util.getStasisLibs()
    try:
        series = sequence_lib.load(util.args[1])
        series.logdir = util.logdir
    except stasis.XMLValidationError, e:
        sterr = "Failed to parse file: %s\n %s" % (util.args[1], e)
        util.logger.error(sterr)
        raise e
                                            
    util.setReporters(series)
    if not util.options.test:
        result = util.runSeries(series)
    else:
        result = series.textList()

    return result
