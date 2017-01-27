
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
import getpass

GROUP = "Testopia"

def intro():
    return ["Run a test cases in tesopia TestRun"]

def abbreviation():
    return "ttr"

def setOptions(parser, stasis):
    parser.set_usage("stasis run-test-case [options] <run_id>")
    parser.add_option("-A", "--arg",
                       action="append",
                       metavar="<var>=<value>",
                       dest="arg_list",
                       help="Variable and value to be passed to test run.")
    parser.add_option("-L", "--logdir", 
                      metavar="PATH",
                      help="Directory to place files from run in")
    parser.add_option("-n", "--no-ssl",
                      metavar="T/F",
                      dest="no_ssl",
                      action="store_true",
                      help="Do NOT use SSL to connecto to testopia server")
    parser.add_option("-P", "--password", 
                      metavar="PASSWORD",
                      help="Password for account on testopia server")
    parser.add_option("-p", "--path", 
                      metavar="/PATH",
                      help="Path on testopia server to cgi script")
    parser.add_option("-o", "--port", 
                      metavar="INT",
                      help="Port on testopia server.")
    parser.add_option("-S", "--server", 
                      metavar="HOSTNAME",
                      help="Hostname of testopia server")
    parser.add_option("-s", "--suite",
                      dest="suite_list",
                      action="append",
                      metavar="FILE",
                      help="Suite to search for sequence file")
    parser.add_option("-U", "--username", 
                      metavar="USER",
                      help="Account name on testopia server")
    parser.add_option("-u", "--url", 
                      metavar="URL",
                      help="URL for testopia server: http[s]://username:password@hostname/path ")
    parser.add_option("-y", "--cycle", 
                      type="int",
                      metavar="INT",
                      help="Number of times a test case is run.")
    
    parser.set_defaults(arg_list=[])
    parser.set_defaults(path="/tr_xmlrpc.cgi")
    parser.set_defaults(logdir=None)
    parser.set_defaults(no_ssl=False)
    parser.set_defaults(password=None)
    parser.set_defaults(port=None)
    parser.set_defaults(server=None)
    parser.set_defaults(suite_list=[])
    parser.set_defaults(username=None)
    parser.set_defaults(url=None)
    parser.set_defaults(cycle=1)

def runCommand(util):
    if len(util.args) < 2:
        sterr = "No case run id provided"
        logger.critical(sterr)
        raise stasis.IncorrectArgument, sterr
    
  
    if util.options.url is None:
        missing = ""
        if util.options.server is None:
            missing = "server"
        
        if util.options.username is None:
            sys.stdout.write("Enter username: ")
            username = sys.stdin.readline().strip()
        else:
            username = util.options.username
           
        if util.options.password is None:
            password = util.stasis.getPassword(util.options.username)
            if password is None:
                password = getpass.getpass("For %s enter password: " % username)
        else: 
            password = util.options.password

        if len(missing) != 0:
            sterr = "No url or %s options provided" % missing
            logger.critical(sterr)
            raise stasis.IncorrectArgument, sterr
        else:
            if util.options.no_ssl:
                protocol = "http"
            else:
                protocol = "https"
            
            url = util.stasis.buildUrl(util.options.server, username,\
                           password, util.options.path, protocol,\
                           util.options.port)
    else:
        url = util.options.url

    if util.options.logdir is None:
        dir_name = "stasis-testiopa-run-%s-%s" % (pwd.getpwuid(os.getuid())[0],
                                    datetime.datetime.now().
                                    strftime("%b-%d-%H%M"))
        logdir = os.path.join(tempfile.gettempdir(), dir_name)
    else:
        logdir = util.options.logdir
    
    case_lib, sequence_lib = util.getStasisLibs() 
    try:
        series = sequence_lib.load(util.args[1], url)
        series.logdir = logdir
    except stasis.XMLValidationError, e:
        sterr = "Failed to parse file: %s\n %s" % (seq_file, e)
        logger.error(sterr)
        raise e
                                            
    if util.options.test:
        result = series.textList()
    else:
        logger.info("logdir %s", logdir)
        if not os.path.isdir(logdir):
            os.mkdir(logdir)
                
        testopia_reporter = stasis.TestopiaCaseReporter(url)
        #stasis.addReporters(series, logdir, options.verbose, options.console, \
        #                    testopia_reporter)
        #result = stasis.runSeries(series, options.arg_list, options.cycle,\
        #                            options.roles)
        util.setReporters(series, testopia_reporter)
        result = util.runSeries(series)

    return result
    
