
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
"""Library for reporting results from running test cases
"""

import pdb
import logging
import sys
import pickle
import codecs

# FIXME: This should be done better
from stasis_abstract import *
from stasis_exceptions import *
from stasis_testopia import *

class TestResult:

    def __init__(self, status, case, msg=None):
        self.status = status
        self.case = case
        self.msg = msg
        
    def report(self, reporter):
        if self.status == STATUS_BEGIN:
            reporter.begin(self.case)
        elif self.status == STATUS_PASS:
            reporter.pass_(self.case, self.msg)
        elif self.status == STATUS_BLOCKED:
            reporter.blocked(self.case, self.msg)
        elif self.status == STATUS_FAIL:
            reporter.fail(self.case, self.msg)
        elif self.status == STATUS_ERROR:
            reporter.error(self.case, self.msg)
        elif self.status == STATUS_TIMEOUT:
            reporter.timeout(self.case, self.msg)
        elif self.status == STATUS_NOTIMPLEMENTED:
            reporter.notImplemented(self.case, self.msg)

    def getTextStatus(self):
        result = None
        if self.status == STATUS_BEGIN:
            result = "Begin"
        elif self.status == STATUS_PASS:
            result = "Pass"
        elif self.status == STATUS_BLOCKED:
            result = "Blocked"
        elif self.status == STATUS_FAIL:
            result = "Fail"
        elif self.status == STATUS_ERROR:
            result = "Error"
        elif self.status == STATUS_TIMEOUT:
            result = "Timeout"
        elif self.status == STATUS_NOTIMPLEMENTED:
            result = "Not implemented"

        return result
        

class TestopiaCaseReporter(TestCaseReporter):
    """A TestCaseReporter that reports to Testopia"""

    def __init__(self, url):
        self._server = TestopiaServer(url)

    def begin(self, case):
        """Signal that the specified test case began"""
        pass

    def pass_(self, case, msg):
        """Signal that the specified test case passed"""
        if not case.hasCaseRunId():
            raise TestopiaError, "No case-run-id for: %s" % case.getName()

        changes = {"case_run_status_id":self._server.passed, "notes":msg}
        self._server.setTestCaseRun(case.getCaseRunId(), changes)

    def fail(self, case, msg):
        """Signal that the specified test case failed"""
        if not case.hasCaseRunId():
            raise TestopiaError, "No case_run_id for: %s" % case.getName()

        changes = {"case_run_status_id":self._server.failed, "notes":msg}
        self._server.setTestCaseRun(case.getCaseRunId(), changes)

    def blocked(self, case, msg):
        """Signal that the specified test case passed"""
        if not case.hasCaseRunId():
            raise TestopiaError, "No case-run-id for: %s" % case.getName()

        changes = {"case_run_status_id":self._server.blocked, "notes":msg}
        self._server.setTestCaseRun(case.getCaseRunId(), changes)

    def error(self, case, msg):
        """Signal that the specified test case resulted in an error"""
        self.fail(case, msg)

    def timeout(self, case, msg):
        """Signal that the specified test case timedout"""
        pass

    def notImplemented(self, case, msg):
        """Signal that the test case has not been implemented"""
        if not case.hasCaseRunId():
            raise TestopiaError, "No case-run-id for: %s" % case.getName()

        changes = {"case_run_status_id":self._server.blocked, "notes":msg}
        self._server.setTestCaseRun(case.getCaseRunId(), changes)

class LoggingTestCaseReporter(TestCaseReporter):
    def __init__(self, debug):
        try:
            level = [logging.ERROR, logging.WARN, logging.INFO][debug - 1]
        except IndexError:
            level = logging.INFO

        self._logger.setLevel(level)

    def begin(self, case):
        """Report test case begin to log file"""
        self._logger.info(u"BEGIN [%s]" % (case.getName()))

    def pass_(self, case, msg):
        """Report test case pass to log file"""
        self._logger.warn(u"PASS [%s]" % (case.getName()))
        self._logger.info(u"%s" % (msg))

    def fail(self, case, msg):
        """Report test case failure to log file"""
        self._logger.error(u"FAIL [%s]" % (case.getName()))
        self._logger.warn(u"%s" % (unicode(msg)))

    def blocked(self, case, msg):
        """Report test case blocked to log file"""
        self._logger.error(u"BLOCKED [%s]" % (case.getName()))
        self._logger.warn(u"%s" % (unicode(msg)))

    def error(self, case, msg):
        """Report test case error to log file"""
        self._logger.error(u"ERROR [%s]" % (case.getName()))
        self._logger.warn(u"%s" % (unicode(msg)))

    def timeout(self, case, msg):
        """Report test case error to log file"""
        self._logger.error(u"TIMEOUT [%s]" % (case.getName()))
        self._logger.warn(u"%s" % (unicode(msg)))

    def notImplemented(self, case, msg):
        """Report test case not implemented to log file"""
        self._logger.error(u"NOT IMPLEMENTED [%s] %s" % (case.getName(), unicode(msg)))

class LogTestCaseReporter(LoggingTestCaseReporter):
    """A TestCaseReporter that reports to a log file"""
    def __init__(self, debug=1, logfile=None):
        self._logger = logging.getLogger("LogTestCaseReporter")
        if logfile is None:
            logfile = "./stasislog"
        
        file_handler = logging.StreamHandler(codecs.open(logfile,
                                                         mode='a',
                                                         encoding='utf-8'))
        file_handler.setFormatter(logging.Formatter("[%(asctime)s]\n %(message)s\n"))
        self._logger.addHandler(file_handler)
        LoggingTestCaseReporter.__init__(self, debug)

class ConsoleTestCaseReporter(LoggingTestCaseReporter):
    """A TestCaseReport that reports to the console"""
    def __init__(self, debug=1):
        self._logger = logging.getLogger("ConsoleTestCaseReporter")
        file_handler = logging.StreamHandler(sys.stdout)
        file_handler.setFormatter(logging.Formatter("%(message)s\n"))
        self._logger.addHandler(file_handler)
        LoggingTestCaseReporter.__init__(self, debug)

class PickleReporter(TestCaseReporter):
    #FIXME this class needs work.
    """A TestCaseReporter that reports to a file format we can read back
    in later for run replay"""
    
    def __init__(self, filename="stasis-run.pickle"):
        self._log = []
        self._filename = filename
        
    def _writeFile(self):
        pickle.dump(self._log, open(self._filename, "wb"))
    
    def begin(self, case):
        self._log.append(TestResult(STATUS_BEGIN, case))
        self._writeFile()
            
    def pass_(self, case, msg):
        self._log.append(TestResult(STATUS_PASS, case, msg))
        self._writeFile()
        
    def blocked(self, case, msg):
        self._log.append(TestResult(STATUS_BLOCKED, case, msg))
        self._writeFile()
        
    def fail(self, case, msg):
        self._log.append(TestResult(STATUS_FAIL, case, msg))
        self._writeFile()
        
    def error(self, case, msg):
        self._log.append(TestResult(STATUS_ERROR, case, msg))
        self._writeFile()
        
    def timeout(self, case, msg):
        self._log.append(TestResult(STATUS_TIMEOUT, case, msg))
        self._writeFile()
        
    def notImplemented(self, case, msg):
        self._log.append(TestResult(STATUS_NOTIMPLEMENTED, case, msg))
        self._writeFile()
        

class DatabaseTestCaseReporter(TestCaseReporter):
    """A TestCaseReporter that reports to a database

    Note: (in theory) it hasn't been implemented yet
    """
    pass

