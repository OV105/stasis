
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
"""Library with abstract classes
"""

from stasis_exceptions import *
import os
import sys
import inspect
import xml.dom.minidom
import ConfigParser

DEFAULT_CONF_DIR_LIST = ["/etc/stasis", os.path.expanduser("~/stasis/conf")]
DEFAULT_DIR_LIST = [os.path.expanduser("~/stasis/test_run_files"),
                    os.getcwd()]
                    
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_BLOCKED = "BLOCKED"
STATUS_ERROR = "ERROR" 
STATUS_TIMEOUT = "TIMEOUT"
STATUS_NOTIMPLEMENTED = "NOTIMPLEMENTED"
STATUS_BEGIN = "BEGIN"
STATUS_NOTRUN = "NOTRUN"

STATUS_LIST = [STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED, STATUS_ERROR,\
             STATUS_TIMEOUT, STATUS_NOTIMPLEMENTED, STATUS_BEGIN, STATUS_NOTRUN]
# don't assume that the first child of the document node is an element!
# this function fixes the bug where if you put a comment before the
# root element, STASIS would choke.
def firstElementChild(node):
    for child in node.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            return child

class TestCaseReporter(object):
    """Abstract class for test case reporting

    Subclasses should implement specific reporting functionality
    """

    def begin(self, case):
        """Signal that the specified test case began"""
        pass

    def pass_(self, case, msg):
        """Signal that the specified test case passed"""
        pass

    def fail(self, case, msg):
        """Signal that the specified test case failed"""
        pass

    def error(self, case, msg):
        """Signal that the specified test case resulted in an error"""
        pass

    def timeout(self, case, msg):
        """Signal that the specified test case timedout"""
        pass

    def notImplemented(self, case, msg):
        """Signal that the test case has not been implemented"""
        pass


class XMLValidator(object):
    """Validates an XML file against a W3C XML Schema

    The object is initialized with an .xsd file defining the XML schema
    to match.
    """

    def __init__(self, xsd_file):
        self._xsd_file = xsd_file

    def validate(self, xml_file):
        """Validate the XML against the XSD defined XML schema

        Returns tuple in the form (status, output) where status is the success
        (0) or failure (non-zero) of the operation and output is an error output
        in the event of failure.
        """
        #if SKIP_VALIDATION:
        #    return (0, '')
        cmd = "xmllint --schema %s %s" % (self._xsd_file, xml_file)
        status, output = commands.getstatusoutput(cmd)
        return (status, output)


class Reader(object):
    """Reads an object, generally an XML file, transforming it into Python objects.

    """

    def __init__(self):
        self._factories = []
        self._registerFactories()

    def _registerFactories(self):
        raise AbstractMethod, "_registerFactory method must be implemented in subclasses."

    def registerFactory(self, factory):
        if inspect.isbuiltin(factory) or inspect.ismethod(factory):
            raise TypeError, "Must enter a factory class, got: %s" % type(factory)
        
        found_make = False
        found_test = False
        for name, member in inspect.getmembers(factory):
            if name == "make":
                found_make = True
            elif name == "test":
                found_test = True
            else:
                continue
                
            try:
                member.im_func()
            except AbstractMethod:
                raise TypeError, "No implementation for method: %s" % (name)
            except TypeError:
                pass 
            except AttributeError:
                raise TypeError, "No %s method found" % (name)
        
        if found_make:
            if found_test:
                self._factories.append(factory)
            else: 
                raise TypeError, "No test() method in class"
        else:
            raise TypeError, "No make() method in class"

    def getFactories(self):
        return self._factories

    def read(self, *args, **kwds):
        """Process the specified data returning a TestCase object

        This function will build a TestCase object out of an XML file.  The XML
        file must match the defined XML Schema.
        """
        if len(self._factories) == 0:
            raise FactoryError, "No factories registered"

        factory = None
        for fact in self._factories:
            if fact.test(*args, **kwds):
                factory = fact
                break
        
        if factory is None:
            raise TypeError, "No factory found for args: %s, kwds: %s" %\
                                                    (args, kwds)

        return factory.make(*args, **kwds)
        
class TestLibrary(Reader):
    """Represents a library of tests"""
    def __init__(self, suite_names=None):
        self.conf_args = {}
        self._versions = {None:None, "stasis_default": None}
        for dir in DEFAULT_CONF_DIR_LIST:
            if os.path.isdir(dir):
                for file in os.listdir(dir):
                    if file[0] != '.':
                        #skip hidden files
                        self._addConfFile(os.path.join(dir,file))
       
        self.setSuiteNames(suite_names)
        Reader.__init__(self)

    def setSuiteNames(self, suite_names=None):
        """Set suite names"""
        if type(suite_names) is list: 
            if len(suite_names) != 0:
                self.suite_names = suite_names
            else:
                self._setSuiteNames()
        elif suite_names is not None:
            self.suite_names = [suite_names]
        else:
            self._setSuiteNames()
       
    def _setSuiteNames(self):
        raise AbstractMethod

    def _load(self, test_obj, suite):
        test_obj.setProperty("suite_name", suite)
        test_obj.setProperty("version", self._versions[suite])
        for (key, value) in self.conf_args.items():
            test_obj.values[key] = value

        return test_obj

    def load(self, *args, **kwds):
        """Load tests into library

        Implement this in a concrete subclasses"""
        raise AbstractMethod
         
    def list(self, suite_names=None):
        """List tests in library

        Implement this in a concrete subclasses"""
        raise AbstractMethod
         
    def addConfFile(self, file):
        self._addConfFile(file)

    def _addConfFile(self, file):
        """Add a config file

        Implement this in a concrete subclasses"""
        raise AbstractMethod

    def getSuiteNames(self):
        return self.suite_names 

class Factory(object):
    """Abstract class for making Python objects out of DOM elements

    Subclasses of this are implemented to handle the creation of a particular
    python class from the corresponding DOM element.
    """
    def __init__(self, load_callback=None):
        self.archive_extn = [u".tar.gz",u".tgz",u".gz",u".tar.bz2",u".bz2"]
        if load_callback is None:
            def null(*args, **kwds): 
                pass

            self.load_callback = null
        else:
            self.load_callback = load_callback
        

    def _parseArgs(self, *args, **kwds):
        result = []
        for i in range(len(self.key_var)):
            try:
                result.append(args[i])
            except IndexError:
                i = i - 1
                break

        for j in range(i+1, len(self.key_var)):
            try:
                result.append(kwds[self.key_var[j]])
            except KeyError:
                result = []
                break

        for i in range(len(result)):
            if type(result[i]) is str:
                try:
                    result[i] = int(result[i])
                except ValueError:
                    try:
                        result[i] = float(result[i])
                    except ValueError:
                        result[i] = unicode(result[i])

        return result
        
    def testFile(self, file, extensions=None):
        result = False
        if type(file) is unicode:
            if os.path.isfile(file):
                if extensions is not None:
                    extn = os.path.splitext(file)[1][1:]
                    if extn in extensions:
                        result = True
                else:
                    result = True

        return result

    def findFile(self, file, paths):
        path = None
        if os.path.isabs(file):
            path = file
            dir = os.path.dirname(file)
        else:
            file_name = file
            for dir in paths:
                search_path = os.path.join(dir, file_name)
                if os.path.exists(search_path):
                    path = search_path
                    break
        
            if path is None:
                dir = None

        return (path, dir)
        
    def findArchiveFile(self, name, paths):
        path = None
        for extn in self.archive_extn:
            path = self.findFile(name+extn, paths)
            if path is not None:
                break
       
        return path

    def readXmlFile(self, xml_file_path):
        filename = os.path.split(xml_file_path)[1]        
        try:
            status, errors = self._xml_validator.validate(xml_file_path)
        except AttributeError:
            pass
        else:
            if status:
                raise XMLValidationError, "In %s:\n%s" % (xml_file_path, errors)
        doc = xml.dom.minidom.parse(xml_file_path)
        return firstElementChild(doc)

    def make(self, *args, **kwds):
        raise AbstractMethod

    def test(self, *args, **kwds):
        raise AbstractMethod


class SourceHandler(object):
    def __init__(self, *args, **kwds):
        self.name = None
        self.filename = None
        self.function_name = None
        self.module_name = None
        self._setParamSrc(*args, **kwds)
        
    def _runInner(self):
        raise AbstractMethod

    def run(self, arg_dict={}, wait_before_kill=600):
        raise AbstractMethod

    def _setParamSrc(self):
        raise AbstractMethod
        
    def getName(self):
        raise AbstractMethod

    #def getParamList(self):
    #    return self._param_list
    def processArgs(self, passed_args):
        return self._param_list.processArgs(passed_args)

    def getCode(self):
        result = ""
        try:
            result = self._src.getCode()
        except AttributeError:
            result = "module file: %s\nfunction: %s" % (self._mod.__file__, \
                                                        self._src.__name__)

        return result

