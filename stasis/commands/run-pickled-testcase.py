
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
import cPickle

GROUP = "Test case execution:"

def intro():
    return ["Run a pickled test case"]

def abbreviation():
    return "rpt"

def setOptions(parser, stasis):
    parser.set_usage("stasis run-test-case [options] <pickled test case file>")
    parser.add_option("-A", "--arg",
                      action="append",
                      metavar="<var>=<value>",
                      dest="arg_list",
                      help="Variable and value to be passed to test run.")
    parser.add_option("-e", "--extension",
                      help="New extension to append to pickle files")
    parser.add_option("-L", "--logdir", 
                      metavar="PATH",
                      help="Directory to place files from run in")
    
    parser.set_defaults(arg_list=[])
    parser.set_defaults(extension=None)
    parser.set_defaults(logdir=None)
    parser.remove_option("--role")
    parser.remove_option("--register")
    parser.remove_option("--i18n")

def runCommand(util):
    if len(util.args) == 0:
        sterr = "No pickled test case file provided"
        logger.critical(sterr)
        raise stasis.IncorrectArgument, sterr
  

    if not util.options.test:
        util.logger.info("logdir %s", util.logdir)
        if not os.path.isdir(util.logdir):
            os.mkdir(util.logdir)
        
        arg_dict = util.getArgDict()
       
    result = []
    for arg in util.args[1:]:
        if os.path.isfile(arg) and os.access(arg, os.R_OK):
            fd = open(arg, 'r')
            tc = cPickle.load(fd)
            fd.close()
        else:
            raise StasisException, "Cannot read file: %s" % arg
        
        if util.options.test:
            result = tc.getProperty('filename')
            if result is None:
                result = tc.getName()
        
            result.append("%s\n\n%s" % (result, tc.getSourceHandler().getCode()))
        else:
            tc.run(arg_dict, util.options.timeout)
            if util.options.extension is None:
                fd = open(arg, 'w')
            else:
                fd = open("%s.%s" % (arg, util.options.extension), 'w')

            cPickle.dump(tc, fd)
            fd.close()
            result.append("Ran test case: %s" % tc.getName())

    return result
