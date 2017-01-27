
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
import ConfigParser
import pwd

GROUP = "Testopia"

def intro():
    return ["Save a testopia test run to a conf file"]

def abbreviation():
    return "tsr"

def setOptions(parser, stasis):
    parser.set_usage("stasis run-test-case [options] <run_id>")
    parser.add_option("-A", "--arg",
                       action="append",
                       metavar="<var>=<value>",
                       dest="arg_list",
                       help="Variable and value to be passed to test run.")
    parser.add_option("-f", "--conf-file",
                      dest="conf_file",
                      metavar="FILE",
                      help="File to save conf file to")
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
    parser.add_option("-R", "--role",
                      action="append", 
                      metavar="<role>=<address>",
                      dest="roles",
                      help="Specify a machine running staf.")
    parser.add_option("-r", "--port", 
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
    
    parser.set_defaults(arg_list=[])
    parser.set_defaults(conf_file=None)
    parser.set_defaults(path="/tr_xmlrpc.cgi")
    parser.set_defaults(no_ssl=False)
    parser.set_defaults(password=None)
    parser.set_defaults(roles=[])
    parser.set_defaults(port=None)
    parser.set_defaults(server=None)
    parser.set_defaults(suite_list=[])
    parser.set_defaults(username=None)
    parser.set_defaults(url=None)

def runCommand(util):
    xsd_dir = os.path.join(os.path.dirname(stasis.__file__), "xsd")
    if len(parsed_args) < 1:
        sterr = "No case run id provided"
        logger.critical(sterr)
        raise stasis.IncorrectArgument, sterr
    
  
    if options.url is None:
        missing = ""
        if options.server is None:
            missing = "server"
        
        if options.username is None:
            missing = "username,%s" % missing
           
        if options.password is None:
            password = stasis.getPassword(options.username)
            if password is None:
                missing = "password,%s" % missing

        if len(missing) != 0:
            sterr = "No url or %s options provided" % missing
            logger.critical(sterr)
            raise stasis.IncorrectArgument, sterr
        else:
            if options.no_ssl:
                protocol = "http"
            else:
                protocol = "https"
            
            url = stasis.buildUrl(options.server, options.username, \
                                  options.password, options.path, protocol, \
                                  options.port)
    else:
        url = options.url

    case_lib, sequence_lib = stasis.getStasisLibs(xsd_dir, 
                                                  options.suite_list,
                                                  options.config_files)
    try:
        series = sequence_lib.load(None, parsed_args[1], url)
    except stasis.XMLValidationError, e:
        sterr = "Failed to parse file: %s\n %s" % (seq_file, e)
        logger.error(sterr)
        raise e
                                            
    #result = series.textList()
    if options.conf_file is None:
        file_name = "stasis-testiopa-%s-%s-%s" % (parsed_args[1],
                                    pwd.getpwuid(os.getuid())[0],
                                    datetime.datetime.now().
                                    strftime("%b-%d-%H%M"))
        conf_file = os.path.join(tempfile.gettempdir(), file_name)
    else:
        conf_file = options.conf_file

    parser = ConfigParser.SafeConfigParser()
    for tc in series:
        tc.addConfSection(parser)

    try:
        fd = open(conf_file, 'w')
    except IOError, strerr:
        fd.close()
        result = "Failed to open %s, Error: %s" % (conf_file, strerr)
    else:
        parser.write(fd)
        fd.close()
        result = "Test series saved to: %s" % (conf_file)

    return result   
