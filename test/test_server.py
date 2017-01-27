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
import pdb
#import re
import optparse

from SimpleXMLRPCServer import SimpleXMLRPCServer
#import threading

#class TestServer(threading.Thread):
class TestServer:
    test_case_run_list = [{"assignee":"tim@ximian.com",
                "build_id":11,
                "case_id":2,
                "case_run_id":3,
                "case_run_status":"IDLE",
                "case_text_version":4,
                "close_date":"2006-12-31 12:34:56",
                "iscurrent":0,
                "notes":"My Note",
                "run_id":5,
                "sortkey":"Sort Key",
                "testedby":"tim@ximian.com"},
               {"assignee":"tim@ximian.com",
                "build_id":11,
                "case_id":22,
                "case_run_id":33,
                "case_run_status":"IDLE",
                "case_text_version":4,
                "close_date":"2006-12-31 12:34:56",
                "iscurrent":0,
                "notes":"My Note",
                "run_id":5,
                "sortkey":"Sort Key",
                "testedby":"tim@ximian.com"},
               {"assignee":"tim@ximian.com",
                "build_id":11,
                "case_id":222,
                "case_run_id":333,
                "case_run_status":"IDLE",
                "case_text_version":4,
                "close_date":"2006-12-31 12:34:56",
                "iscurrent":0,
                "notes":"My Note",
                "run_id":5,
                "sortkey":"Sort Key",
                "testedby":"tim@ximian.com"},
               {"assignee":"tim@ximian.com",
                "build_id":11,
                "case_id":2222,
                "case_run_id":3333,
                "case_run_status":"IDLE",
                "case_text_version":4,
                "close_date":"2006-12-31 12:34:56",
                "iscurrent":0,
                "notes":"My Note",
                "run_id":5,
                "sortkey":"Sort Key",
                "testedby":"tim@ximian.com"},
               {"assignee":"tim@ximian.com",
                "build_id":11,
                "case_id":22222,
                "case_run_id":33333,
                "case_run_status":"IDLE",
                "case_text_version":4,
                "close_date":"2006-12-31 12:34:56",
                "iscurrent":0,
                "notes":"My Note",
                "run_id":5,
                "sortkey":"Sort Key",
                "testedby":"tim@ximian.com"},
                ]

    def __init__(self, port, count, debug_level=0, filename=None):
        self.case_run_list = []
        self.id_dict = {2:3,22:33,222:333,2222:3333,22222:33333}
        for case_id in [2,22,222,2222]:
            self.case_run_list.append({
                'build_id': 84,
                'environment_id': 8,
                'testedby': '',
                'run_id': 104, 
                'notes': '',
                'sortkey': 0, 
                'assignee': 5621, 
                'case_id': case_id,
                'close_date': '', 
                'iscurrent': 1, 
                'case_run_id': self.id_dict[case_id],
                'case_text_version': 1, 
                'case_run_status_id': 1})
        
        self.testcaserun_status_id = {"PASSED":2,"FAILED":3,"BLOCKED":4}
        self.logger = logging.getLogger( "TestCase" )
        #self.logger.setLevel( 30 - debug_level * 10 )
        level = [logging.ERROR, logging.INFO, logging.DEBUG][debug_level]
        self.logger.setLevel(level)
        if filename is None:
            handler = logging.StreamHandler()
        else:
            handler = logging.FileHander(filename, "w")

        formatter = logging.Formatter("%(name)s():%(lineno)s\n %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.port = port
        self.count = count
        #threading.Thread.__init__(self)
        self.server = SimpleXMLRPCServer(("localhost", self.port))
        self.server.register_introspection_functions()
        self.server.register_function(self.testListMethods,"listMethods")
        self.server.register_function(self.testCaseGet,"TestCase.get")
        self.server.register_function(self.testCaseRunGet,"TestCaseRun.get")
        self.server.register_function(self.testCaseRunList,"TestCaseRun.list")
        self.server.register_function(self.testCaseRunUpdate,"TestCaseRun.update")
        self.server.register_function(self.testCaseLookUpStatusName,"TestCase.lookup_status_id_by_name")
        self.server.register_function(self.testCaseRunLookUpStatusName,"TestCaseRun.lookup_status_id_by_name")

    #def run(self):
    def start_server(self):
        old_name = self.logger.name
        self.logger.name = "run"
        if self.count == 0:
            self.logger.info("self.count == 0")
            while True:
                self.logger.debug("Got request")
                self.server.handle_request()
        else:
            for i in range(self.count):
                self.logger.debug("Before handle_request()")
                self.server.handle_request()
            self.logger.info("Finished request count")
       
        self.logger.name = old_name
    
    def testListMethods(self):
        old_name = self.logger.name
        self.logger.name = "testListMethods"
        self.logger.info("Method called")
        return ["listMethods",
                "TestCase.get",
                "TestCaseRun.get",
                "TestCaseRun.list",
                "TestCaseRun.update",
                "TestCase.lookup_status_id_by_name"]
        self.logger.name = old_name
    
    def testCaseLookUpStatusName(self, name):
        old_name = self.logger.name
        self.logger.name = "testCaseLookUpStatusName"
        self.logger.info("name: %s", name)
        result = 1
        if name == "CONFIRMED":
            self.logger.debug("name matched 'CONFIRMED'")
            result = 2
        else:
            pass
            #FIXME return error

        self.logger.name = old_name
        return result

    def testCaseRunLookUpStatusName(self, name):
        old_name = self.logger.name
        self.logger.name = "testCaseRunLookUpStatusName"
        self.logger.info("name: %s", name)
        try:
            result = self.testcaserun_status_id[name]
        except KeyError:
            result = 1
            self.logger.error("name: %s not in testcaserun_status_id", name)
            #FIXME return error

        self.logger.name = old_name
        return result
        
    def testCaseRunGet(self, id):
        old_name = self.logger.name
        self.logger.name = "testCaseRunGet"
        self.logger.info( "id: %s", id)
        result = {}
        if id == 3:
            self.logger.name = old_name
            result = self.case_run_list[0]
        elif id == 33:
            self.logger.name = old_name
            result = self.case_run_list[1]
        elif id == 333:
            self.logger.name = old_name
            result = self.case_run_list[2]
        else:
            self.logger.error("id: %s, not matched", id)
        
        self.logger.name = old_name
        self.logger.debug("result: %s", result)
        return result

    def testCaseRunList(self, id):
        old_name = self.logger.name
        self.logger.name = "testCaseRunList"
        self.logger.info("id: %s", id)
        self.logger.name = old_name
        #return self.test_case_run_list
        return self.case_run_list
                
    def testCaseRunUpdate(self, run_id, case_id, build_id, env_id, changes):
        old_name = self.logger.name
        self.logger.name = "testCaseRunUpdate"
        self.logger.info("run_id: %s, case_id: %s, build_id: %s, changes:\n%s",\
                          run_id, case_id, build_id, changes)
        result = {"faultcode":"1","faultstring":"Failed to update"}
        if (run_id == 104) and (case_id == 22 or case_id == 2)\
           and (build_id == 84):
            if changes["case_run_status_id"] in self.testcaserun_status_id.values()\
               and changes.has_key("notes"):
                result = self.testCaseRunGet(self.id_dict[case_id])
            else:
                self.logger.error("Failed to update")
        
        self.logger.name = old_name
        print result
        return result

    def testCaseGet(self, id):
        old_name = self.logger.name
        self.logger.name = "testCaseGet"
        self.logger.info("id: %s", id)
        automated_status = 1;
        xml_file = "case_pass_%s.xml" % (id)
        case_status_id = 2
        if id == 222:
            #function test case
            xml_file = "test_case_pass_func"
        if id == 2222:
            self.logger.debug("Not automated test case")
            automated_status = 0;
            xml_file = ""
        elif id == 22222:
            self.logger.debug("Not confirmed test case")
            case_status_id = 1
        else:
            self.logger.debug("Automated test case")

        self.logger.name = old_name
        return {
            'requirement': '',
            'default_tester_id': 5621,
            'plans': [{'plan_id': 135, 'name': 'Stan test plan', 'type_id': 3, 'creation_date': '2006-10-10 12:54:04', 'default_product_version': 'all', 'author_id': 5621, 'isactive': 1, 'product_id': 54}], 
            'script': xml_file, 
            'priority_id': 6, 
            'creation_date': '2006-10-10 13:05:29', 
            'sortkey': 13331, 
            'summary': "Summary for %s" % xml_file,
            'alias': '',
            'case_id': 15426, 
            'case_status_id': case_status_id, 
            'author_id': 5621, 
            'category_id': 327, 
            'isautomated': automated_status, 
            'canview': 1, 
            'arguments': 'stasis_unittest'
        }

def main( args ):
    sys.path.append(os.path.realpath("."))
    base_name = os.path.splitext( os.path.basename(sys.argv[0]) )[0]
    usage = "usage: %prog -p port [-c count] [-l filename]"
    #parser = stasis.OptionParser( usage=usage )
    parser = optparse.OptionParser( usage=usage )
    parser.add_option("-c", "--count",
                       type="int",
                       default=1,
                       help="Count of requests", 
                       action="store" )
    parser.add_option("-l", "--logfile", 
                       default=None,
                       help="Log filename", 
                       action="store" )
    parser.add_option("-p", "--port", 
                       type="int",
                       default=8222,
                       help="Port number", 
                       action="store" )
    parser.add_option("-v", "--verbose", 
                       action="count", 
                       dest="debug_level", 
                       default=0, 
                       help="Increase verbosity of debug output")

    (options,args) = parser.parse_args()
    print "starting server on port: %s" % options.port
    server = TestServer( options.port, options.count, options.debug_level, options.logfile )
    server.start_server()

if __name__ == '__main__':
    main( sys.argv[1:] )

