
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
"""Library for running XML based test sequences

High level example usage:

    import nrmxtest

    case_lib = nrmxtest.TestCaseLibrary()
    case_lib.addConfFile("/home/alice/stasis.conf")

    sequence_lib = nrmxtest.TestSequenceLibrary(case_lib)
    sequence_lib.addConfFile("/home/alice/stasis.conf")

    sequence = sequence_lib.load("test-sequence-1.xml")
    console_reporter = nrmxtest.ConsoleTestCaseReporter()
    sequence.addReporter(console_reporter)
    runner = nrmxtest.Runner(sequence)
    runner.run()
"""

import logging
import sys
import tempfile
import xml.dom.minidom
import commands
import os.path
import exceptions
import time
import cPickle
import codecs
import inspect
import ConfigParser
import socket
import re
import datetime
import threading
import copy
import Queue
from base64 import encodestring

# FIXME: This should be done better
from stasis_exceptions import *
from stasis_abstract import *
from stasis_source_handlers import *
from stasis_testopia import *
from stasis_reports import *

USING_STAF = True
try:
    #import PySTAF
    import staf
except ImportError:
    USING_STAF = False

def changeEncoding():
# Not elegant code but it allows us to build one RPM For all distributions
# and platforms. This is the only platform-specific thing we need to do.
    if sys.getdefaultencoding() != 'utf-8':
        import textwrap
        lib_dir = filter(lambda p: p[-3:]==sys.version[:3], sys.path)[0]
        cmd = os.path.basename(sys.argv[0])
        sitecust_filename = os.path.join(lib_dir, 'sitecustomize.py')
        intro = textwrap.fill("%s detected that your system's default string encoding is \
not set to UTF-8.  Probably this is the first time you have run %s.\n" % \
        (cmd, cmd))
        if os.geteuid() == 0:
            cust_filename = sitecust_filename
            mode = 'a'
            fix_text = "This has been fixed by editing the file:\n\n  %s\n\n\
You can now rerun %s." % (cust_filename, cmd)
        else:
            cust_filename = os.path.expanduser("~/sitecustomize.py")
            mode = 'w'
            fix_text = "The fix for this issue has been stored in:\n\n  %s\n\n\
In order for %s to run these changes must be appended to:\n\n  %s\n\n " % \
                        (cust_filename, cmd, sitecust_filename)

        sitecust = open(cust_filename, mode)
        sitecust.write("\n\n")
        sitecust.write("### START CHANGES BY %s ###\n" % (cmd))
        sitecust.write("import sys\n")
        sitecust.write("sys.setdefaultencoding('utf-8')\n")
        sitecust.write("### END CHANGES BY %s ###\n" % (cmd))
        sitecust.close()
        raise EncodingError, "%s %s" % (intro, fix_text)
        
RUN_TYPES = ["all","paused","failed","notrun","passed"]
LIST_TYPES = ["list","tree"]

def getTestCaseName(*args, **kwds):
    """Takes either file-name or module + function"""
    values = list(args)
    try:
        values.append(kwds['file'])
        if len(values) > 1:
            raise TypeError, "only single arg for file, got: %s, %s" \
                                % (args, kwds)
    except KeyError:
        pass

    try:
        values.insert(0, kwds['module'])
    except KeyError:
        pass

    try:
        values.append(kwds['function'])
    except KeyError:
        pass

    for i in range(len(values)):
        if type(values[i]) is int:
            values[i] = str(values[i])

    if len(values) == 1:
        result = os.path.basename(values[0])
    elif len(values) == 2:
        result = "%s+%s" % tuple(values)
    else:
        raise TypeError, "only (file) or (module,function) args, got: %s, %s"\
                            % (args, kwds)
    return result

def splitTestCaseName(name):
    return name.split("+")

def getFunctionFromName(name):
    parts = name.split("+")
    if len(parts) == 2:
        result = parts[1]
    else:
        result = None

    return result

def getModuleFromName(name):
    parts = name.split("+")
    if len(parts) == 2:
        result = parts[0]
    else:
        result = None

    return result

######################################################################
# Start Common classes
######################################################################
class SysInfoFactory:
    def __init__(self):
        self.info_class_list = [SuseSysInfo, RpmSysInfo]

    def make(self):
        result = None
        for info_class in self.info_class_list:
            result = info_class.test()
            if result is not None:
                break

        return result

class SysInfo(object):
    def __init__(self, dict=None):
        self._property_keys = []
        self._addPropertyKeys()
        self._properties = {}
        for key in self._property_keys:
            self._properties[key] = None

        if dict is None:
            self.loadSysInfo()
        else:
            self.loadDict(dict)

    def _addPropertyKeys(self):
        self._property_keys.extend(['distro', 'platform', 'arch', \
                               'python_version', 'ram'])

    def loadSysInfo(self):
        self._properties["python_version"] = sys.version_info

    def test(cls):
        result = cls._testSystem()
        if result:
            return cls()
        else:
            return None

    def _testSystem():
        return True

    _testSystem = staticmethod(_testSystem)
    test = classmethod(test)

    def loadDict(self, dict):
        for key in dict.keys():
#FIXME test value type also
            if key in self._property_keys:
#FIXME ? raise error instead of skipping keys
                self._properties[key] = dict[key]

        #self._properties = dict.copy()

    def getProp(self, prop_name):
        if self._properties.has_key(prop_name):
            return self._properties[prop_name]
        else:
            return None

class LinuxSysInfo(SysInfo):
    def _addPropertyKeys(self):
        self._property_keys.extend(['cpus', \
                               'cpu_model_name', 'cpu_speed', 'cpu_vendor', \
                               'cpu_family', 'cpu_model', 'kernel_release', \
                               'kernel_machine',  'hostname', 'alias_list', \
                               'ipaddr_list'])

    def loadSysInfo(self):
        SysInfo.loadSysInfo(self)
        self._properties["platform"] = "linux"
        (status, out) = commands.getstatusoutput("uname -r")
        if status == 0:
            self._properties["kernel_release"] = out
        else:
            raise SysInfoError, "Command failed: `uname -r`"

        (status, out) = commands.getstatusoutput("uname -m")
        if status == 0:
            self._properties["kernel_machine"] = out
        else:
            raise SysInfoError, "Command failed: `uname -m`"


        if os.path.isfile("/proc/meminfo"):
            lines = [s.strip().split(":") for s in open("/proc/meminfo").readlines()]
            for line in lines:
                if line[0].strip() == "MemTotal":
                    self._properties["ram"] = line[1].strip().split(' kB')[0]
                    break
        else:
            raise SysInfoError, "No /proc/meminfo file found"

        (self._properties["hostname"], self._properties["host.alias_list"], \
                            self._properties["host.ipaddr_list)"]) = \
                            socket.gethostbyname_ex(socket.gethostname())

        if os.path.isfile("/proc/cpuinfo"):
            #lines = [s.strip() for s in open("/proc/cpuinfo").readlines()]
            lines = [s.strip().split("\t: ") for s in open("/proc/cpuinfo").readlines()]
            self._properties["cpus"] = 0
            for line in lines:
                title = line[0].strip()
                if title == 'processor':
                    self._properties["cpus"] += 1
                elif title == "model name":
                    self._properties["cpu_model_name"] = line[1]
                elif title == "cpu MHz":
                    self._properties["cpu_speed"] = line[1]
                elif title == "vendor_id":
                    self._properties["cpu_vendor"] = line[1]
                elif title == "cpu family":
                    self._properties["cpu_family"] = line[1]
                elif title == "model":
                    self._properties["cpu_model"] = line[1]
        else:
            raise SysInfoError, "No /proc/cpuinfo file found"


    def _testSystem():
        result = SysInfo._testSystem()
        if sys.platform[:5] != "linux":
            result = False

        return result

    _testSystem = staticmethod(_testSystem)

class RpmSysInfo(LinuxSysInfo):
    def _addPropertyKeys(self):
        LinuxSysInfo._addPropertyKeys(self)
        self._property_keys.extend(['rpm_list'])

    def loadSysInfo(self):
        LinuxSysInfo.loadSysInfo(self)
        self._properties["rpm_list"] = {}
        (status, out) = commands.getstatusoutput("rpm -qa --qf='%{name} %{version} %{release}\n'")
        if status == 0:
            for (name, ver, rel) in [s.split(' ') for s in out.split("\n")]:
                self._properties["rpm_list"][name] = (ver, rel)
        else:
            raise SysInfoError, "Command failed: `rpm -qa`"

    def _testSystem():
        result = LinuxSysInfo._testSystem()
        (status, out) = commands.getstatusoutput("rpm --version")
        if status != 0:
            result = False
        
        return result

    _testSystem = staticmethod(_testSystem)

    def certify(self, requirements_dict):
        for (key, value) in requirements_dict.iteritems():
            if not self._properties.has_key(key):
                return False

            if key == "rpm_list":
                this_rpm_names = self._properties["rpm_list"].keys()
                this_rpm_dict = self._properties["rpm_list"] 
                for req_name in values.keys(): 
                    if not req_name in this_rpm_names:
                        return False

                    if values[req_name][0] is not None:
                        if values[req_name][0] != this_rpm_dict[req_name][0]:
                            return False
                    
                    if values[req_name][1] is not None:
                        if values[req_name][1] != this_rpm_dict[req_name][1]:
                            return False

            elif value != self._properties[key]:
                return False

        return True

class SuseSysInfo(RpmSysInfo):
    def _addPropertyKeys(self):
        RpmSysInfo._addPropertyKeys(self)
        self._property_keys.extend(['suse-release-lines'])

    def loadSysInfo(self):
        RpmSysInfo.loadSysInfo(self)
        if os.path.isfile("/etc/SuSE-release"):
            self._properties["distro"] = "suse"
            self._properties["suse-release-lines"] = [s.strip() for s in open("/etc/SuSE-release").readlines()]
        else:
            raise SysInfoError, "Cannot find /etc/SuSE-release file"

    def _testSystem():
        if os.path.isfile("/etc/SuSE-release"):
            return True
        else:
            return False

    _testSystem = staticmethod(_testSystem)

class FileTestLibrary(TestLibrary):
    """Represents a library of tests located in files"""

    def __init__(self, suite_names=None):
        self._paths = {"stasis_default":[]}
        #self._versions = {"stasis_default": None}

        for dir in DEFAULT_DIR_LIST:
            if os.path.isdir(dir):
                self.addPath(dir)
        
        if sys.path.count(os.getcwd()) == 0:
            sys.path.append(os.getcwd())
            
        TestLibrary.__init__(self, suite_names)

    def _setSuiteNames(self):
        self.suite_names = self._paths.keys()
            
    def _addConfFile(self, file):
        """Add a config file"""
        try:
            #FIXME check if file exists
            config = ConfigParser.SafeConfigParser()
            config.read(file)
            for sect in config.sections():
                if self._versions.has_key(sect):
                    if sect != "stasis_default":
                        raise "Duplicate config file section: %s" % sect
                self._versions[sect] = None
                for (key,value) in config.items(sect):
                    if key == "_search_paths":
                        dirs = value.split(":")
                        if self._paths.has_key(sect):
                            self._paths[sect].extend(dirs)
                        else:
                            self._paths[sect] = dirs
                    elif key == "_module_paths":
                        dirs = value.split(":")
                        for dir in dirs:
                            if sys.path.count(dir) == 0:
                                sys.path.append(dir)
                    elif key == "_version":
                        self._versions[sect] = value
                    else:
                        self.conf_args[key] = value
        except Exception, e:
            #FIXME handle errors
            print "Conf File error: %s" % e

    def addPath(self, path, suite_name=None):
        """Add a path to be included in the library"""
        if suite_name is None:
            suite_name = "stasis_default"

        if self._paths.has_key(suite_name):
            self._paths[suite_name].append(path)
        else:
            self._paths[suite_name] = [path]

    def getPaths(self):
        result = []
        for suite in self.suite_names: 
            result.extend(self._paths[suite])
            
        return result

    def getPathTo(self, filename, suite_names=None):
        def findFile(suite, filename):
            if not self._paths.has_key(suite):
                raise "Do not have section: %s" % suite

            for dir in self._paths[suite]:
                search_path = os.path.join(dir, filename)
                if os.path.exists(search_path):
                    return search_path

            return None 
        
        if suite_names is None or len(suite_names) == 0:
            suite_names = self.suite_names
         
        if type(suite_names) is list:
            for suite in suite_names:
                path_to_file = findFile(suite, filename)
                if path_to_file:
                    break
        else:
            path_to_file = findFile(suite_names, filename)
            
        #if not path_to_file:
        #    raise FileNotFound, filename
            #FIXME for testopia set 
        return path_to_file
                
    def _seq_callback(self, seq_file_name, suite_names=None):
        if suite_names is not None:
            self.setSuiteNames(suite_names)

        return self.load(seq_file_name)

    def load(self, *args, **kwds): 
        """Loads a Test object from the library"""
        test_obj = self.read(paths=self.getPaths(), *args, **kwds)
        test_obj_suite = None
        try:
            path = test_obj._source_handler.path
            for suite in self.suite_names:
                for dir in self._paths[suite]:
                    if dir == path:
                        test_obj_suite = suite
                        break

                if test_obj_suite is not None:
                    break
            #FIXME raise error if path not found?
        except AttributeError:
            pass

        return TestLibrary._load(self, test_obj, test_obj_suite)

    def list(self, suite_names=None):
        """Return a sorted list of files available in the library"""
        if suite_names is None:
            suite_names = self.suite_names 

        result = []
        for suite in suite_names:
            for path in self._paths[suite]:
                for fname in os.listdir(path):
                    fnsplit = os.path.splitext(fname)
                    if fnsplit[1] == ".xml":
                        result.append(fname)
        result.sort()
        return result

######################################################################
# End Common classes
######################################################################

######################################################################
# Start Test Case classes
######################################################################
class TestCaseProperties(dict):
    filters = {'testopia':['build_id', 'environment_id', 'testedby', \
                            'run_id', 'notes', 'sortkey', 'assignee',\
                            'case_id', 'close_date', 'iscurrent',\
                            'case_run_id', 'case_text_version', \
                            'case_run_status_id'],
               'default':['type', 'val', 'trace', 'stdout_err', \
                          '_tmp_ini_file', 'function_name', 'module_name', \
                          'filename', 'suite_name', 'version',\
                          'status', 'role','msg','blocks-all','collective']}
    def __init__(self, default=None):
        self.default = default
        dict.__init__(self)
        for key in self.filters['default']:
            self[key] = self.default
        
    def filtercopy(self, name):
        list = self.filterkeys(name)
        result = {}
        for key in list:
            result[key] = self.get(key)

        return result
    
    def filteritems(self, name=None):
        if name is None:
            name = 'default'
        
        result = []
        for key in self.filterkeys(name):
            result.append((key, self.get(key)))

        return result
           
    def filterkeys(self, name=None):
        if name is None:
            name = 'default'

        return self.filters[name]

    def get(self, key, *args):
        if not args:
            arg = (self.default)
        
        return dict.get(self, key, arg)
        
class TestCase(object):
    """Represents a test case

    To initialize a TestCase object, you must specify:
    
    name - the exact tcdb name of the test case in the specified folder
    param_list - a ParamList object containing required test case Params
    source - a Source object containing the test case source code
    source_handler - a SourceHandler object which can handle the source
    """
    __name__ = "TestCase"
    def __init__(self, source_handler, role=None, setup=None, teardown=None):
        self._properties = TestCaseProperties()
        self._properties['status'] = STATUS_NOTRUN
        self._properties['filename'] = source_handler.filename
        self._properties['module_name'] = source_handler.module_name
        self._properties['function_name'] = source_handler.function_name

        self._properties['role'] = role
        self._source_handler = source_handler
        self.values = {}
        self.substitutions = {}
        self.depends_on = []
        self.setup = setup
        self.teardown = teardown
        self.search_paths = []
        fd, temp_file = tempfile.mkstemp(suffix=".ini", prefix="stasis_")
        os.close(fd)
        try:
            os.remove(temp_file)
        except OSError:
            pass

        self._properties['_tmp_ini_file'] = temp_file

    def getTestCasesToRun(self, tc=None):
        result = [] 
        if self._properties['status'] is STATUS_NOTRUN:
            if tc is not None:
                self.updateDependsOn(tc)

            if len(self.depends_on) == 0:
                self.setStatus(STATUS_BEGIN)
                result.append(self)

        return result

    def updateDependsOn(self, tc):
        if tc.getStatus() == STATUS_PASS or (tc.getStatus() == STATUS_BEGIN \
                    and  tc.hasProperty("background")):
            if tc.getName() in self.depends_on:
                self.depends_on.remove(tc.getName())

        elif tc.getStatus() == STATUS_FAIL or \
                    tc.getStatus() == STATUS_ERROR or \
                    tc.getStatus() == STATUS_BLOCKED or \
                    tc.getStatus() == STATUS_TIMEOUT:
            if tc.hasProperty("blocks-all") or tc.getName() in self.depends_on:
                if self.getStatus() == STATUS_NOTRUN:
                    self.setStatus(STATUS_BLOCKED)
                    self.setProperty("msg", \
                                "Blocked by test case: %s, with status: %s" %\
                                (tc.getName(), tc.getStatus()))
                
        else:
            #FIXME add entry for BEGIN ?
            pass
        
    def setDependsOn(self, tc):
        if not tc.getName() in self.depends_on:
            self.depends_on.append(tc.getName())

    def getSectionName(self, filter=None, name=None):
        if filter is None:
            filter = "default"

        if name is None:
            name = self.getName()
        
        return "%s/%s" % (name, filter)

    def addConfSection(self, parser, filters=None):
        name = self.getName()
        if filters is None:
            filters = self._properties.filters.keys()
        elif filters.count('default') == 0:
            filters.append('default')

        for filter in filters:
            filt_sect = self.getSectionName(filter)
            parser.add_section(filt_sect)
            for key,value in self._properties.filteritems(filter):
                if value is not None:
                    parser.set(filt_sect, key, unicode(value))
                else:
                    parser.set(filt_sect, key, '')
        
        if len(self.values) != 0:
            val_sect =  self.getSectionName(filter="values")
            parser.add_section(val_sect)
            for key,value in self.values.iteritems():
                parser.set(val_sect, key, unicode(value))    
            
        if len(self.substitutions) != 0:
            subst_sect =  self.getSectionName(filter="substitutions")
            parser.add_section(subst_sect)
            for key,value in self.substitutions.iteritems():
                parser.set(subst_sect, key, unicode(value))

    def loadConf(self, parser):
        for filter in self._properties.filters.keys():
            sect_name = self.getSectionName(filter)
            if not parser.has_section(sect_name):
                continue
                
            for key,value in parser.items(sect_name):
                #FIXME check for empty values       
                #FIXME change property
                self.setProperty(unicode(key), unicode(value))
        
        #FIXME create source handler?
        val_sect =  self.getSectionName(filter="values")
        if parser.has_section(val_sect):
            for key,val in parser.items(val_sect):
                self.values[unicode(key)] = unicode(val)

        subst_sect =  self.getSectionName(filter="substitutions")
        if parser.has_section(subst_sect):
            for key,val in parser.items(subst_sect):
                self.substitutions[unicode(key)] = unicode(val)
                

    #make this a more general process for all properties
    def setCaseRunId(self, case_run_id):
        """Return the case_run_id for Testopia"""
        try:
            self._properties['case_run_id'] = int(case_run_id)
        except ValueError:
            raise TypeError, "case_run_id must be int or unicode, not %s" % \
                              type(case_run_id)

    def getCaseRunId(self):
        """Return the case_run_id for Testopia"""
        return self._properties['case_run_id']

    def hasCaseRunId(self):
        try:
            int(self._properties['case_run_id'])
        except TypeError:
            return False
        except ValueError:
            return False
        except KeyError:
            return False
        
        return True
        
    def getName(self):
        """Return the name of the test case"""
        return self._source_handler.getName(self._properties["suite_name"])

    def getStatus(self):
        """Return the name of the test case"""
        return self._properties['status']

    def setStatus(self, status):
        """Return the name of the test case"""
        if status in STATUS_LIST:
            self._properties['status'] = status
        else:
            raise TypeError, "Not a recognized status: %s" % status

    def getParamList(self):
        """Return the list of parameters that the test case accepts"""
        return self._source_handler.getParamList()

    def hasProperty(self, key):
        if self._properties.has_key(key):
            if self._properties[key] is not None:
                return True

        return False

    def setProperty(self, key, value):
        if key is None:
            pass
        else:
            if value == '':
                value = None

            self._properties[key] = value

    def getProperty(self, key):
        try:
           result = self._properties[key]
        except KeyError:
            result = None

        return result

    def processRule(self, subst_key, arg_dict):
        """Process substitution rule

        Currently only substitutes the value of one arg for an other. May be 
        extended in the future
        """
        result = None
        if arg_dict.has_key(self.substitutions[subst_key]):
            result = arg_dict[self.substitutions[subst_key]]
        else:
            pass
            #FIXME raise exception ?

        return result

    def getSourceHandler(self):
        return self._source_handler

    def processPassedArgs(self, passed_args):
        arg_dict = self.values.copy()
        for arg_key in passed_args.keys():
            arg_dict[arg_key] = passed_args[arg_key]

        for subst_key in self.substitutions.keys():
            subst_value = self.processRule(subst_key, arg_dict)
            if subst_value != None or not arg_dict.has_key(subst_key):
                arg_dict[subst_key] = subst_value

        try:
            self.arguments = self._source_handler.processArgs(arg_dict)
        except MissingParameter, strerr:
            self._properties["type"] = None 
            self._properties["val"] = "missing parameter: %s" % (strerr)
            self._properties["trace"] = '' 
            self._properties["stdout_err"] = ''
            self._properties["status"] = STATUS_FAIL
            self._properties["msg"] = self.getProperty('val')
            return False
        else:
            return True


    def run(self, passed_args, wait_before_kill):
        """Run the test case

        Runs the test case, signaling all associated reporters to the result.
        """
        if self.processPassedArgs(passed_args):
            self.wait_before_kill = wait_before_kill
            if self.setup is not None:
                setup_args = passed_args.copy()
                setup_args["_run_callback"] = self._callback
                setup_args["_base_test_case_name"] = self.getName()
                setup_args["_search_paths"] = self.search_paths
                setup_args["_function_name"] = getFunctionFromName(self.getName())
                setup_args["_module_name"] = getModuleFromName(self.getName()) 
                self.setup.setStatus(STATUS_BEGIN)
                self.setup.run(setup_args, wait_before_kill)
                if self.setup.getStatus() != STATUS_PASS:
                    self.setStatus(STATUS_FAIL)
                    self._properties["type"] = self.setup.getProperty("type")
                    self._properties["val"] = self.setup.getProperty("val")
                    self._properties["trace"] = self.setup.getProperty("trace")
                    self._properties["stdout_err"] = \
                                     self.setup.getProperty("stdout_err")
                    self._properties["status"] = self.setup.getProperty("status")
                    self._properties["msg"] =  self.setup.getProperty("msg")
                elif os.path.isfile(self._properties["_tmp_ini_file"]):
                    # run only if not run by setup
                    parser = ConfigParser.SafeConfigParser()
                    fd = open(self._properties["_tmp_ini_file"], 'r')
                    parser.readfp(fd)
                    fd.close()
                    if parser.has_section(self.getSectionName()):
                        self.loadConf(parser)
                    os.remove(self._properties["_tmp_ini_file"])
                    
                else:
                    self._runInner()
            else:
                self._runInner()

            if self.teardown is not None:
                self.teardown.run(setup_args, wait_before_kill)
    
    def _callback(self):
        self._runInner()
        parser = ConfigParser.SafeConfigParser()
        self.addConfSection(parser)
        fd = open(self._properties["_tmp_ini_file"], 'w')
        parser.write(fd)
        fd.close()

    def _runInner(self):
        if self._source_handler is None:
            self._properties["type"] == "NOTIMPLEMENTED"
        else:
            (type, val, trace, stdout_err) =  self._source_handler.run(\
                                        self.arguments, self.wait_before_kill)
            self._properties["type"] = type
            self._properties["val"] = val
            self._properties["trace"] = trace
            self._properties["stdout_err"] = stdout_err
            
        #FIXME filter only last X number of lines
        if type == "PASSED":
            self._properties["status"] = STATUS_PASS
            self._properties["msg"] = "%s\n%s" % (val, stdout_err)
        elif type == "TIMEDOUT":
            self._properties["status"] = STATUS_FAIL
            self._properties["msg"] = "Test timed out\n%s" % (stdout_err)
        elif type == "NOTIMPLEMENTED" or \
                    isinstance(type, TestNotImplemented):
            self._properties["status"] = STATUS_NOTIMPLEMENTED
            self._properties["msg"] = "Test not implemented"
        elif type == None:
            self._properties["status"] = STATUS_FAIL
            self._properties["msg"] = "Raised: %s\n%s" % (val, stdout_err)
        elif isinstance(type, AssertionFailure):
            self._properties["status"] = STATUS_FAIL
            self._properties["msg"] = "%s\n%s\n%s" % (val, "".join(trace), stdout_err)
        elif isinstance(type, exceptions.KeyboardInterrupt) or \
                            isinstance(type, exceptions.SystemExit):
            raise type
        else:
            self._properties["status"] = STATUS_FAIL
            self._properties["msg"] = \
                 "Unknown failure: %s\nError: %s\nTrace:\n==========\n%s" % (\
                  type, val, "".join(trace))

    def report(self, reporter):
        if self._properties["status"] == STATUS_BEGIN:
            reporter.begin(self)
        elif self._properties["status"] == STATUS_PASS:
            reporter.pass_(self, self._properties["msg"])
        elif self._properties["status"] == STATUS_BLOCKED:
            reporter.blocked(self, self._properties["msg"])
        elif self._properties["status"] == STATUS_FAIL:
            reporter.fail(self, self._properties["msg"])
        elif self._properties["status"] == STATUS_ERROR:
            reporter.error(self, self._properties["msg"])
        elif self._properties["status"] == STATUS_TIMEOUT:
            reporter.timeout(self, self._properties["msg"])
        elif self._properties["status"] == STATUS_NOTIMPLEMENTED:
            reporter.notImplemented(self, self._properties["msg"])

    
    def getCount(self, status):
        if self._properties["status"] == status:
            return 1
        else:
            return 0

    def print_tree(self, depth=0):
        for i in xrange(depth * 4):
            sys.stdout.write(" ")
        print self.getName()


class XMLTestCaseFactory(Factory):
    """Creates TestCase instances out of test-case DOM elements"""
    key_var = ['file', 'paths']
    
    def __init__(self, load_callback):
        self._source_handler_reader = SourceHandlerReader()
        Factory.__init__(self, load_callback)

    def make(self, *args, **kwds):
        """Return a TestCase instance"""
        def getTestCase(xml_element, type):
            try:
                elm = xml_element.getElementsByTagName(type)[0]
            except IndexError:
                tc = None
            else:
                filename = elm.getAttribute("file")
                if filename == '':
                    func = elm.getAttribute("function")
                    mod = elm.getAttribute("module")
                    tc = self.load_callback(mod, func)
                else:
                    tc = self.load_callback(filename)
            return tc

        (filename, paths) = self._parseArgs(*args, **kwds)
        (file, dir) = self.findFile(filename, paths)

        
        xml_element = self.readXmlFile(file)
        source_handler = self._source_handler_reader.read(xml_element, \
                                        os.path.basename(filename), dir)
        tc = TestCase(source_handler)
        tc.search_paths = paths
        tc.setup = getTestCase(xml_element, "setup")
        if tc.setup is not None:
            tc.setup.setProperty("_base_test_case_name", tc.getName())

        tc.teardown = getTestCase(xml_element, "teardown")
        if tc.teardown is not None:
            tc.teardown.setProperty("_base_test_case_name", tc.getName())

        return tc

    def test(self, *args, **kwds):
        values = self._parseArgs(*args, **kwds)
        if len(values) == 0:
            return False
            
        (file, paths) = values
        if type(file) is not unicode:
            return False

        (file_path, dir) = self.findFile(file, paths)
        if file_path is None:
            return False
            
        if not self.testFile(file_path, ['xml']):
            return False

        return True
        
class PickleTestCaseFactory(Factory):
    """Creates TestCase instances out of test-case DOM elements"""
    key_var = ['file']
    
    def make(self, *args, **kwds):
        """Return a TestCase instance"""
        file = self._parseArgs(*args, **kwds)
        tc = cPickle.load(open(file))
        return tc

    def test(self, *args, **kwds):
        values = self._parseArgs(*args, **kwds)
        if len(values) != 1:
            return False
            
        file = values
        if type(file) is not unicode:
            return False

        if not os.path.isfile(file): 
            return False
            
        try:
            cPickle.load(open(file))
        except:
            return False

        return True
        
class FunctionTestCaseFactory(Factory):
    key_var = ['module','function','paths']
    
    """Creates TestCase shims containing Python function references."""
    def make(self, *args, **kwds):
        """
        Takes a module name and the name of a function in that module and 
        creates a TestCase that will run that function."""

        (module,function,paths) = self._parseArgs( *args, **kwds)
        name = getTestCaseName(module, function)

        source_handler = FunctionSourceHandler(module, function)
        tc = TestCase(source_handler)
        if function != "setup" and function != "teardown":
            try:
                tc.setup = self.load_callback(module, "setup")
            except:
                tc.setup = None
            
            try:
                tc.teardown = self.load_callback(module, "teardown")
            except:
                tc.teardown = None

        tc.search_paths = paths
        tc.isFunctionTestCase = 1
        return tc

    def test(self, *args, **kwds):
        values = self._parseArgs( *args, **kwds)
        if len(values) == 0:
            return False
        
        (module,function,paths) = values
        if type(module) is not unicode or type(function) is not unicode:
            return False
            
        try:
            mod = __import__(module)
        except ImportError:
            return False

        try:
            src = getattr(mod, function)
        except AttributeError:
            return False

        return True

class TestCaseLibrary(FileTestLibrary):
    """Represents a library of test cases"""

    def __init__(self, case_validator, suite_names=None):
        self._case_validator = case_validator
        FileTestLibrary.__init__(self, suite_names)

    def _registerFactories(self):
        self.registerFactory(XMLTestCaseFactory(self.load))
        self.registerFactory(FunctionTestCaseFactory(self.load))
        #self.registerFactory(PickleTestCaseFactory(self.load))

######################################################################
# End Test Case classes
######################################################################



######################################################################
# Start Runner classes
######################################################################
class RoleRegistry:
    """Basically a singleton class that allows you to register a number
    of remote machines with "roles" such as 'server', 'workstation',
    'zlmclient', etc.  Test sequences can specify that the machine 
    currently fulfilling a certain role should execute a certain test
    case or sequence."""

    def __init__(self, list=[], role=None):
        self.default_role = role
        self.setHosts(list)

    def setHosts(self, list):
        self._registry = {}
        self.addHosts(list)

    def addHosts(self, list):
        for item in list:
            self.addRole(item)

    def addHost(self, item):
        if type(item) is list:
            if len(item) == 1:
                role = None
                host = item[0]
            elif len(item) == 2:
                role = item[0]
                host = item[1]
            else:
                raise TypeError, "Incorrect format for role: %s" % item
        elif type(item) is str:
            role = None
            host = item
        else:
            raise TypeError, "Role must be string or list not: %s" % item

        if self._registry.has_key(role):
            if self._registry[role].count(host) == 0:
                self._registry[role].append(host)
        else:
            self._registry[role] = [host]
   
    def getHosts(self, role=None):
        if role is None:
            role = self.default_role

        if self._registry.has_key(role):
            result = self._registry[role]
        else:
            result = []
                
        return result

    def getAllHosts(self):
        result = []
        for host_list in self._registry.itervalues():
            result.extend(host_list)

        return result

    def getRoles(self):
        result = self._registry.keys()
        return result

    def isEmpty(self):
        return len(self._registry) == 0
    

    def getAddress(self, role):
        if not self.isRoleRegistered(role):
            return "127.0.0.1"
        else:
            return RoleRegistry._registry[role]

    def isRoleRegistered(self, role):
        return RoleRegistry._registry.has_key(role)


class RunDispatcher:
    MAX_THREADS = 1
    DEFAULT_TIMEOUT = 600
    #DEFAULT_MAX_THREADS = 20
    def __init__(self, test_series, rr, passed_args={}, timeout=None,):
        self.test_series = test_series
        self.rr = rr
        self.passed_args = passed_args
        if timeout is None:
            self.timeout = RunDispatcher.DEFAULT_TIMEOUT
        else:
            self.timeout = timeout

        self.to_be_run = {}
        self.done = Queue.Queue()
        self.on_deck = []
        self.run_count = 0
        #self.events = {}
        #self.running_threads = []
        self.runner_list = []
        #self.threads_semaphore = threading.Semaphore()
        #self.threads_semaphore.acquire(False):
        #self.this_machine = SysInfo()
        if USING_STAF and not self.rr.isEmpty():
            self.using_staf = True 
            for role in self.rr.getRoles():
                self.addRole(role)
        else:
            to_do = Queue.Queue()
            self.to_be_run[None] = to_do
            self.using_staf = False
            for count in range(self.MAX_THREADS):
                runner = Runner(self.passed_args, self.timeout, to_do,\
                                self.done)
                self.runner_list.append(runner)


    def addRole(self, role):
        to_do = Queue.Queue()
        self.to_be_run[role] = to_do

        for host in self.rr.getHosts(role):
            runner = Runner(self.passed_args, self.timeout, to_do, self.done,\
                            host)
            self.runner_list.append(runner)

    def run(self):
        """Run the test sequence

        arg_dict - dictionary defining parameter to value bindings
        """
        tc_to_run = []
        for runner in self.runner_list:
            runner.start()

        self.getNewTestCases()
        while self.run_count > 0:
            while True:
                try:
                    tc = self.done.get(timeout=1)
                except Queue.Empty:
                    break
               
                #FIXME add check to see if staf failure, if yes rerun
                self.test_series.updateDependsOn(tc)
                self.run_count -= 1

            self.getNewTestCases()
        
        for runner in self.runner_list:
            runner.kill()
            runner.join()
            del(runner)

        self.test_series.report()

    def hasOpenJobs(self):
        if len(self.on_deck) > 0:
            return True

        for to_do_que in self.to_be_run.itervalues():
            if not to_do_que.empty():
                return True
           
        return False

    def getNewTestCases(self):
        self.on_deck.extend(self.test_series.getTestCasesToRun())
        while True:
            try:
                tc = self.on_deck.pop()
            except IndexError:
                break
                
            if self.using_staf:
                role = tc.getProperty('role')
                if role is None:
                    self.to_be_run[self.rr.default_role].put(tc)
                    self.run_count += 1
                elif self.rr.hasRole(role):
                    self.to_be_run[role].put(tc)
                    self.run_count += 1
                else:
                    tc.setStatus(STASIS_FAIL)
                    tc.setProperty("msg", "Role %s not registered" % role)
                    self.done.put(tc)
            else:
                self.to_be_run[None].put(tc)
                self.run_count += 1
                if not tc.hasProperty("background"):
                    break

class Runner(threading.Thread):
    DEFAULT_TIMEOUT = 6
    def __init__(self, passed_args, wait_before_kill, to_do_queue, done_queue,\
                 host=None):
        threading.Thread.__init__(self)
        self.passed_args = passed_args
        self.wait_before_kill = wait_before_kill
        self.to_do_queue = to_do_queue
        self.done_queue = done_queue
        self.host = host
        #FIXME query from host for this information
        self.host_tmp_dir = "/tmp"
        self.id = "%s-%d-%s" % (socket.getfqdn(), os.getpid(), \
                                self._Thread__name)
        if host is not None:
            self.staf_handle = staf.STAFHandle(self.id)
            self.run_inner = self._runInnerStaf
        else:
            self.staf_handle = None
            self.run_inner = self._runInnerLocal
        
        self.__die = False

    def run(self):
        """Run the associated test with the associated arguments

        Evaluates variables bound to arguments using the parent_scope as
        the available variables.
        """
        while not self.__die:
            tc = None
            try:
                tc = self.to_do_queue.get(timeout=self.DEFAULT_TIMEOUT)
            except Queue.Empty:
                pass

            if tc is not None:
                self.run_inner(tc)
                self.done_queue.put(tc)

        if self.staf_handle is not None:
            del(self.staf_handle)
   
    def kill(self):
        self.__die = True

    def _runInnerLocal(self, tc):
        tc.run(self.passed_args, self.wait_before_kill)

    def _runInnerStaf(self, tc):
        if tc.processPassedArgs(self.passed_args):
            file_name = "%s-%s-%s" % (self.id, tc.getName(), int(time.time()))
            pickle_file = os.path.join(tempfile.gettempdir(), file_name)
            try:
                fd = open(pickle_file, 'w')
            except IOError:
                raise StasisException, "Could not open file %s" % pickle_file 
            
            cPickle.dump(tc, fd)
            fd.close()

            result = self.staf_handle.submit(self.host, "FS", \
                     'COPY FILE %s TODIRECTORY %s TOMACHINE %s' % \
                     (pickle_file, self.host_tmp_dir, self.host)
                     )
            
            #FIXME use dir. separator based on host platform
            host_tc_file = "%s/%s" % (self.host_tmp_dir, file_name)
            #cmd = "/home/tim/work/stasis/scripts/stasis rpt %s" % host_tc_file
            cmd = "stasis rpt %s" % host_tc_file 
            result = self.staf_handle.submit(self.host, "PROCESS", 
                ('START SHELL COMMAND "%s" WAIT %d RETURNFILE %s' % 
                (cmd, self.wait_before_kill * 1000, host_tc_file ))
                )
            
            un = staf.unmarshall(result.result)
            tc_obj=cPickle.loads(un.getRootObject()['fileList'][0]['data'])
            tc._properties = tc_obj._properties
            
            
######################################################################
# End Runner classes
######################################################################


######################################################################
# Start Test series classes
######################################################################

class TestSeries(list, TestCase):
    """Respresents a test sequence

    A TestSequence consists of a RunSequence, and optionally a set of parameters.

    seq - a RunSequence object defining the ordered set of Runners which make
          up the sequence
    params - a ParamList object defining any parameters the sequence requires

    """
    __name__ = "TestSeries"
    def __init__(self, name, collective=False):
        self.conf_file = None
        self._reporters = []
        self.time_stamp = time.time()
        TestCase.__init__(self, EmptySourceHandler(name), name)
        self.setProperty("collective", collective)

    def getTestCasesToRun(self, tc=None):
        result = []
        if self.getProperty("collective") and self.getStatus() == STATUS_FAIL:
            #tc = None
            pass
        else:
            for item in self:
                new_tc = item.getTestCasesToRun(tc)
                result.extend(new_tc)
                #if tc is not None:
                #    break

        return result 
   
    def updateDependsOn(self, tc):
        TestCase.updateDependsOn(self, tc)
        if self.getProperty("collective") and tc in self:
            # make sure tc is from this series
            # One test case failure -> test series failed
            # FIXME add threshhold # of TC that must fail before  series fails.
            if self.getStatus() != STATUS_FAIL:
                if tc.getStatus() == STATUS_FAIL or \
                        tc.getStatus() == STATUS_ERROR or \
                        tc.getStatus() == STATUS_TIMEOUT:
                    self.setStatus(STATUS_FAIL)
                    self.setProperty('msg', \
                         "Failed due to test case: %s, status: %s\n %s" %\
                         (tc.getName(), tc.getStatus(), tc.getProperty("msg")))
                elif tc.getStatus() == STATUS_PASS:
                    self.setStatus(STATUS_PASS)
                    self.setProperty('msg', "%s\n%s" % (self.getProperty('msg')\
                                     ,"Test Case passed: %s" % (tc.getName())))
                elif tc.getStatus() == STATUS_BLOCKED:
                    self.setProperty('msg', "%s\n%s" % (self.getProperty('msg')\
                                    ,"Test Case blocked: %s" % (tc.getName())))

        for item in self:
            item.updateDependsOn(tc)

    def __hash__(self):
        return hash("%s%i" % (self.getName(), self.time_stamp))


    def __str__(self):
        return "<TestSeries %s-%i>" % (self.getName(), self.time_stamp)

    def addReporter(self, reporter):
        """Add a reporter to the test case.

        Reporter instances that are added here are notified of begin, pass,
        fail, and error signals, and can handle them as they please.
        """
        self._reporters.append(reporter)

    def clearReporters(self):
        self._reporters = []

    def getReporters(self):
        return self._reporters

    def report(self, reporters=None):
        #if self.test_case is None:
        if reporters is None:
            reporters = self._reporters
        elif type(reporters) is not list:
            reporters = [reporters]

        if self.getProperty("collective"):
            for reporter in reporters:
                #self.test_case.report(reporter)
                #self.report(reporter)
                TestCase.report(self, reporter)
        else:
            for tc in self:
                for reporter in reporters:
                    tc.report(reporter)

    def isBlocked(self, name):
        result = False
        for list in self.run_after.itervalues():
            if list.count(name) > 0:
                result = True
                break
        
        return result

    def getAllTestCases(self):
        result = []
        for tc_list in self.itervalues():
            result.extend(tc_list)

        for series in self.child_test_series.keys():
            result.extend(series.getAllTestCases())

        return result

    def printConf(self):
        parser = ConfigParser.SafeConfigParser()
        for tc in self:
            tc.addConfSection(parser)

        parser.write(sys.stdout)

    def textList(self):
        result = ""
        for tc in self:
            result += "%s\n" % tc.getName()

        return result

    def saveConfFile(self, filename=None):
        if filename is None:
            if self.conf_file is None:
                conf_file = os.tempname(prefix="stasis")
            else:
                conf_file = self.conf_file
        else:
            conf_file = filename

        parser = ConfigParser.SafeConfigParser()
        try:
            fd = open(conf_file, 'w')
        except IOError:
            #fd.close()
            conf_file = os.tempnam(prefix="stasis")
            fd = open(filename, 'w')
        else:
            for tc in self:
                tc.addConfSection(parser)

            parser.write(fd)
            fd.close()

        return conf_file

    def getCount(self, status):
        result = 0 
        if status in STATUS_LIST:
            for tc in self:
                result += tc.getCount(status)
        else:
            pass
            #FIXME raise error ?

        return result

class INITestSeriesFactory(Factory):
    key_var = ['file', 'paths']

    def __init__(self, load_callback, case_lib):
        self._case_lib = case_lib
        self._source_handler_reader = SourceHandlerReader()
        Factory.__init__(self, load_callback)


    def test(self, *args, **kwds):
        values = self._parseArgs(*args, **kwds)
        if len(values) != 2:
            return False

        (file, paths) = values
        if type(file) is not unicode:
            return False

        (file_path, dir) = self.findFile(file, paths)
        if file_path is None:
            return False
            
        if not self.testFile(file_path, [u'ini', u'conf']):
            return False

        parser = ConfigParser.SafeConfigParser()
        fd = open(file_path, 'r')
        try:
            parser.readfp(fd)
            fd.close()
        except:
            fd.close()
            return False

        return True
    
    def make(self, *args, **kwds):
        (filename, paths) = self._parseArgs(*args, **kwds)
        (file, dir) = self.findFile(filename, paths)

        series_name = os.path.basename(file)
        parser = ConfigParser.SafeConfigParser()
        fd = open(file, 'r')
        parser.readfp(fd)
        fd.close()
        sections = parser.sections()
        name_list = []
        for section in sections:
            match = re.search("^([^/]*)/default", section)
            if match:
                name_list.append(match.group(1))
        
        #FIXME implement as Reader 
        series = TestSeries(series_name)
        for name in name_list:
            sect_name = "%s/default" % (name)
            try:
                filename = parser.get(sect_name, "filename")
            except ConfigParser.NoOptionError:
                filename = None

            if filename == '' or filename is None:
                try:
                    function = parser.get(sect_name, 'function')
                    module = parser.get(sect_name, 'module')
                except ConfigParser.NoOptionError:
                    function = None
                    module = None

                tc = self._case_lib.load(module, function)
            else:
                tc = self._case_lib.load(filename)
                
            tc.loadConf(parser)
            series.append(tc)

        return series

class XMLTestSeriesFactory(Factory):
    """
    Creates TestSequences out of DOM elements.

    A TestSequenceLibrary and a TestCaseLibrary are required to initialize
    a TestSequenceFactory object.  All test sequences and test case XML files
    that the sequence (and any sub-sequences) will use but me made available in the
    library paths.
    """
    key_var = ['file', 'paths']

    def __init__(self, load_callback, case_lib):
        #self._sequence_lib = sequence_lib
        self._case_lib = case_lib
        Factory.__init__(self, load_callback)
    
    def parseRunElement(self, run_element, values, substitutions):
        #FIXME document that values and substitutions are not recursive to 
        #to any sequences opened from a run element.

        module = None
        function = None
        type = run_element.getAttribute("type")
        file = unicode(run_element.getAttribute("file"))
        
        if file == '':
            module = unicode(run_element.getAttribute("module"))
            function = unicode(run_element.getAttribute("function"))
       
        #FIXME? add suite_name child element to run element for 
        #multiple suite_names.
        if run_element.hasAttribute('suite'):
            suite = unicode(run_element.getAttribute("suite"))
            self._case_lib.setSuiteNames(suite)
        else:
            suite = None

        if run_element.hasAttribute('timeout'):
            timeout = run_element.getAttribute('timeout')
        else:
            timeout = None
      
        arg_list_element = run_element.getElementsByTagName("arg-list")
        if len(arg_list_element) != 0:
            arg_elements = arg_list_element[0].getElementsByTagName('arg')
            for arg_e in arg_elements:
                values[unicode(arg_e.getAttribute('name'))] =\
                            unicode(arg_e.getAttribute('value'))
        
        subst_list_element = run_element.getElementsByTagName("substitute-list")
        if len(subst_list_element) != 0:
            subst_elements = subst_list_element[0].getElementsByTagName('substitute')
            for sub_e in subst_elements:
                rule = unicode(sub_e.getAttribute('source-rule'))
                substitutions[unicode(sub_e.getAttribute('dest-name'))] = rule

        #FIXME role unicode ?
        if run_element.hasAttribute("role"):
            role = run_element.getAttribute("role")
        

        id = run_element.getAttribute("case-run-id")
        if type == "sequence":
            #series = self.load_callback(suite, file)
            series = self.load_callback(file, suite)
            if run_element.hasAttribute("collective"):
                series.setProperty("collective", True)
            result = series
        else:
            try:
                name = None
                if file != '':
                    name = getTestCaseName(file)
                    tc = self._case_lib.load(file)
                else:
                    name = getTestCaseName(module, function)
                    tc = self._case_lib.load(module, function)
            except:
                if id != '':
                    # FIXME setup testcase that will give status
                    # not implemented.
                    tc = TestCase(EmptySourceHandler(), name=name)
                else:
                    raise TestNotImplemented, "Name: %s" % (name)

            if run_element.hasAttribute('background'):
                tc.setProperty("background", True)

            result = tc

        if run_element.hasAttribute("blocks-all"):
            result.setProperty("blocks-all", 1)

        #depends_on_elements = run_element.getElementsByTagName("depends-on")
        # FIXME allow for multiple depends-on elements
        #if len(depends_on_elements) > 0:
        for dep_on_elem in run_element.getElementsByTagName("depends-on"):
            file = dep_on_elem.getAttribute("file")
            if file == '':
                module = dep_on_elem.getAttribute("module")
                function = dep_on_elem.getAttribute("function")
                if module == '' or function == '':
                    pass
                    #FIXME raise error ?
                else:
                    result.depends_on.append(getTestCaseName(module, function))
            else:
                result.depends_on.append(getTestCaseName(file))
        
        result.values = values
        if result.setup:
            result.setup.values = values

        if result.teardown:
            result.teardown.values = values

        result.substitutions = substitutions
        if id != '':
            result.setCaseRunId(id)

            
        return result

    def make(self, *args, **kwds):
        #Return a TestSequence built from specified test-sequence DOM element

        (filename, paths) = self._parseArgs(*args, **kwds)
        (file, dir) = self.findFile(filename, paths)

        xml_element = self.readXmlFile(file)
        values = {}
        substitutions = {}
        name = os.path.basename(file)
        arg_list_element = xml_element.getElementsByTagName("arg-list")
        if len(arg_list_element) != 0:
            arg_elements = arg_list_element[0].getElementsByTagName('arg')
            for arg_e in arg_elements:
                values[unicode(arg_e.getAttribute('name'))] =\
                            unicode(arg_e.getAttribute('value'))

        subst_list_element = xml_element.getElementsByTagName("substitute-list")
        if len(subst_list_element) != 0:
            subst_elements = subst_list_element[0].getElementsByTagName('substitute')
            for sub_e in subst_elements:
                rule = unicode(sub_e.getAttribute('source-rule'))
                substitutions[unicode(sub_e.getAttribute('dest-name'))] = rule

        series = TestSeries(name)
        run_elements = xml_element.getElementsByTagName('run')
        for run_element in run_elements:
            #self.parseRunElement(run_element, values, suite_names)
            #FIXME Document that suite-names entered by load only impact
            #the first sequence xml file loaded
            #series.extend(self.parseRunElement(run_element, values, substitutions))
            series.append(self.parseRunElement(run_element, values,\
                                                substitutions))
            

        return series

    def test(self, *args, **kwds):
        values = self._parseArgs(*args, **kwds)
        if len(values) != 2:
            return False

        (filename, paths) = values
        #if type(file) is not str:
        if type(filename) is not unicode:
            return False

        #file_path = self.findFile(file, paths)
        (file_path, dir) = self.findFile(filename, paths)
        if file_path is None:
            return False
            
        if not self.testFile(file_path, ['xml']):
            return False

        return True

class TestSequenceLibrary(FileTestLibrary):
    """Represents a library of test sequences"""

    def __init__(self, case_lib, suite_names=None): 
        self._case_lib = case_lib
        FileTestLibrary.__init__(self, suite_names)

    def _registerFactories(self):
        self.registerFactory(XMLTestSeriesFactory(self._seq_callback, 
                                                  self._case_lib))
        self.registerFactory(TestopiaSeriesFactory(self._seq_callback, 
                                                  self._case_lib))
        self.registerFactory(INITestSeriesFactory(self._seq_callback, 
                                                  self._case_lib))

    def addPath(self, path, suite_name=None):
        self._case_lib.addPath(path, suite_name)
        FileTestLibrary.addPath(self, path, suite_name)

    def addConfFile(self, file):
        self._case_lib.addConfFile(file)
        TestLibrary.addConfFile(self, file)


######################################################################
# End Test sequence classes
######################################################################


######################################################################
# Start Testopia sequence classes
######################################################################
class TestopiaSeriesFactory(Factory):
    """Reads XML file format test case, transforming it into Python objects"""
    key_var = ['test_run_id', 'url', 'paths']

    def __init__(self, sequence_lib, case_lib):
        self._seq_lib = sequence_lib
        self._case_lib = case_lib
        #self._factory = XMLTestSeriesFactory(sequence_lib, self._case_lib)
        #FIXME change if Testopia ever allows child test runs
        Factory.__init__(self, None)

    def make(self, *args, **kwds):
        (test_run_id, url, paths) = self._parseArgs(*args, **kwds)
        server = TestopiaServer(url) 
        series = TestSeries(test_run_id)
        try:
            seq_name = u"%s-%s" % (test_run_id,time.strftime("%b%d-%H%I"))
            seq_doc = xml.dom.minidom.Document()
            suite_elm = seq_doc.createElement("test-suite")
            suite_elm.setAttribute("name", seq_name)
            seq_elm = seq_doc.createElement("test-sequence")
            suite_elm.appendChild(seq_elm)
            seq_doc.appendChild(suite_elm)
            test_case_runs = server.getTestCasesToRun(test_run_id)
            for test_case_run in test_case_runs:
                test_case = server.getTestCase(test_case_run["case_id"])
                if len(test_case) == 0:
                    raise XMLValidationError, "%s" % test_case_run["case_id"]
                
                run_elm = seq_doc.createElement("run")
                run_elm.setAttribute("case-run-id", 
                                     unicode(test_case_run["case_run_id"]))
                if test_case["isautomated"] == 0:
                    # Create empty test case
                    run_elm.setAttribute("type","case")
                    run_elm.setAttribute("file", '')
                    run_elm.setAttribute("name", 'case_id')
                    tc = TestCase(EmptySourceHandler(), 
                                  getTestCaseName(test_case_run["case_id"]))
                elif os.path.splitext(test_case["script"])[1] == ".xml":
                    if len(test_case["arguments"]) != 0:
                        suite = test_case["arguments"]
                    else:
                        suite = None

                    try:
                        tc = self._case_lib.load(test_case["script"])
                        run_elm.setAttribute("type","case")
                    except TypeError:
                        tc = self._seq_lib.load(test_case["script"])
                        tc.setProperty("collective", True) 
                        run_elm.setAttribute("type","sequence")

                    run_elm.setAttribute("file", unicode(test_case["script"]))
                    if len(test_case["arguments"]) != 0:
                        run_elm.setAttribute("suite",\
                                              unicode(test_case["arguments"]))
                else:
                    run_elm.setAttribute("type","case")
                    run_elm.setAttribute("module",\
                                        unicode(test_case["arguments"]))
                    run_elm.setAttribute("function",\
                                        unicode(test_case["script"]))
                    tc = self._case_lib.load(test_case["arguments"],
                                             test_case["script"])

                for key,value in test_case_run.iteritems():
                    tc.setProperty(key, value)

                series.append(tc)
        except Exception, e:
            print "Error: %s" % e
        
        # create local seq file for rerun 
        xml_file = os.path.join(tempfile.gettempdir(), 
                                    "seq-%s.xml" % (seq_name))
        try:
            fd = open(xml_file, "w")
            seq_doc.writexml(fd)
            fd.close()
        except:
            print "FIXME ERROR here"

        return series
        

    def test(self, *args, **kwds):
        values = self._parseArgs(*args, **kwds)
        if len(values) != 3:
            return False

        (test_run_id, url, paths) = values
        if type(url) is not unicode:
            return False
        #FIXME test url string

        try:
            int(test_run_id) 
        except:
            return False

        return True


######################################################################
# End Testopia sequence classes
######################################################################

def runningWithAction(action):
    """Are we currently running with this action?  See the RunActionList
    documentation for an explanation with examples of how to use this."""
    
    return RunActionList().runningWithAction(action)

class RunActionList:
    """Basically a singleton class that allows you to specify a set of
    'actions' for this run; e.g. 'setup', 'test', 'teardown', etc.  Here
    are the guidelines for these actions, if your test suite is going to
    support them:

    setup:    "Setup" actions should ensure that everything is in the
              correct state to run the actual test case.  They should not
              assume that things are currently in a clean state, and also
              should not make any assertions.

    test:     Here is where you run your actual tests.  All assertions
              should go here, and "test" actions can assume that "setup"
              has already been run.

    teardown: "Teardown" actions should ensure that everything the "setup"
              and "test" actions did is reversed.  Again, they should not
              make assertions, and should not assume that things have not
              already been reversed.

    An example of how to use run actions in your test cases:

    if runningWithAction('setup'):
        os.system('touch /tmp/chowntest.file')

    if runningWithAction('test'):
        s, o = commands.getstatusoutput('chown 603 /tmp/chowntest.file')
        assert_equals(s, 0)
        s, o = commands.getstatusoutput('ls -l /tmp/chowntest.file')
        assert_equals(s, 0)
        assert_match('-rw-r--r--', o)

    if runningWithAction('teardown'):
        os.system('rm -f /tmp/chowntest.file')

    Run actions are case insensitive and can be specified on the command
    line.  By default, we run with the actions 'setup', 'test', and
    'teardown'.
    """

    _actions = []

    def _normalize(self, action):
        return str(action).lower()

    def addAction(self, action):
        action = self._normalize(action)
        if action not in RunActionList._actions:
            RunActionList._actions.append(action)

    def runningWithAction(self, action):
        action = self._normalize(action)
        return (action in RunActionList._actions)

    def removeAction(self, action):
        action = self._normalize(action)
        if action in RunActionList._actions:
            RunActionList._actions.remove(action)

