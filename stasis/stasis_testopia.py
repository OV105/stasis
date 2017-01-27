
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
"""Library for interfacing with Testopia server via xml-rpc
"""

import logging
import xmlrpclib
import socket
import xml.parsers.expat
import re
import string
import os.path
from base64 import encodestring
# FIXME: This should be done better
from stasis_exceptions import *


##############################
#
# Start Tesopia functions
#
##############################
def getPassword(username, filename=None):
    if filename is None:
        filename = os.path.expanduser("~/.ssh/stasis-%s" % (username))

    try:
        fd = open(filename, 'r')
        lines = fd.readlines()
        fd.close()
        result = string.strip(lines[0])
    except:
        result = None

    return result

def buildUrl(hostname, username, password=None,
             cgi="/tr_xmlrpc.cgi", protocol="https",port=None):

    if password is None:
        password = getPassword(username)

    if cgi[0] != '/':
        cgi = "/%s" % cgi

    if port is None:
        return "%s://%s:%s@%s%s" % (protocol,
                                    username,
                                    password,
                                    hostname,
                                    cgi)
    return "%s://%s:%s@%s:%s%s" % (protocol,
                                username,
                                password,
                                hostname,
                                port,
                                cgi)

def hidePassword(url):
    return re.sub(":[^:@]*@", ":*****@", url)

class TestopiaServer:
    def __init__(self, url, debug=0): 
        self.url = url
        self._server = xmlrpclib.ServerProxy(self.url, verbose=debug)
        self.confirmed = self.remoteCmd(self._server.TestCase.lookup_status_id_by_name, "CONFIRMED")
        self.passed = self.remoteCmd(self._server.TestCaseRun.lookup_status_id_by_name, "PASSED")
        self.failed = self.remoteCmd(self._server.TestCaseRun.lookup_status_id_by_name, "FAILED")
        self.blocked = self.remoteCmd(self._server.TestCaseRun.lookup_status_id_by_name, "BLOCKED")

        
    def getTestCasesToRun(self, run_id):
        result = []
        case_run_list = self.getTestCaseRunList(run_id)
        for case_run in case_run_list:
            test_case = self.getTestCase(case_run["case_id"])
            if test_case["isautomated"] == 1 and \
               test_case["case_status_id"] == self.confirmed:
                result.append(case_run)
        
        #print "getTestCasesToRun result: %s" % result
        return result
        
    def getTestCaseRunList(self, run_id):
        result = []
        if type(run_id) is str:
            run_id = int(run_id)
        
        result = self.remoteCmd(self._server.TestCaseRun.list, {"run_id":run_id})
        return result
        
    def getTestCase(self, case_id):
        if type(case_id) is str:
            case_id = int(case_id)
        
        result = self.remoteCmd(self._server.TestCase.get, case_id)
        return result

    def setTestCaseRun(self, case_run_id, changes):
        current = self.remoteCmd(self._server.TestCaseRun.get, case_run_id)
        if type(current) == str:
            raise TestopiaError, "Cannot find case_run_id: %s" % case_run_id
        
        for key in changes.iterkeys():
            if not current.has_key(key):
                raise TestopiaError, "Unknown key: %s" % key
                
        result = self.remoteCmd(self._server.TestCaseRun.update, 
                                current["run_id"], 
                                current["case_id"], 
                                current["build_id"],
                                current["environment_id"],
                                changes)
        if len(result) < len(current):
            raise TestopiaError, "Failed updating case_run_id: %s, Error: %s" %\
                                  (case_run_id, result["faultstring"])

        return result

    def remoteCmd(self, cmd, *args):
        try:
            if len(args) == 1:
                result = cmd(args[0])
            #elif len(args) == 2:
            #    result = cmd(args[0], args[1])
            else:
                result = cmd(args[0], args[1], args[2], args[3], args[4])
            
        except socket.gaierror, e:
            #problems connecting to host
            #FIXME raise TestopiaException hidePassword(self._url_ 
            result = []
        except xmlrpclib.Fault, e:
            #problems with query
            result = []
        except xml.parsers.expat.ExpatError, e:
            result = []
        except socket.sslerror:
            # no ssl support on server
            # FIXME raise error
            result = []

        return result
       
##############################
#
# End Tesopia functions
#
##############################


