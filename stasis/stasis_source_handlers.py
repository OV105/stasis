
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
"""Library for running the source code for test cases
"""

import pdb
import logging
import sys
import tempfile
import commands
import traceback
import time
import pickle
import inspect
import signal
import datetime
import shutil
import types

from stasis_abstract import *
from stasis_exceptions import *

class PipeSignalHandler:
    def __init__(self, std_fd_wr, wr):
        self.std_fd_wr = std_fd_wr
        self.wr = wr

    def cleanUp(signum, stackframe):
        self.std_fd_wr.flush()
        self.std_fd_wr.close()
        os.write(self.wr, pickle.dumps(("TIMEOUR", "Timed out", stackframe)))
                #traceback.format_exception(etype, evalue, etraceback))))

def runWithTimeout(code, timeout):
    """This is our third (or so) try at a test case runner.  It supports
    relatively safe out-of-process execution and a timeout - now with
    100% less race conditions."""
   
    #FIXME create 2nd pipe to capture stdout, stderr.
    rd, wr = os.pipe()
    std_rd, std_wr = os.pipe()
    signum = 6

    pid = os.fork()
    if pid:
        # this is the parent

        # the parent doesn't need to write
        os.close(wr)
        os.close(std_wr)
        std_file = os.fdopen(std_rd)

        exitedpid = 0
        poll_interval = 0.5
        start_time = time.time()
        end_time = start_time + timeout
        while (exitedpid == 0) and (time.time() < end_time):
            exitedpid, status = os.waitpid(pid, os.WNOHANG)
            if not exitedpid:
                time.sleep(poll_interval)


        if not exitedpid:
            # child still going!
            os.kill(pid, signum)
            # reap the child
            os.waitpid(pid, 0)
            stdout_stderr = std_file.read()
            std_file.close()
            #raise TimeOutException("child had to be killed with kill -9")
            etype = "TIMEDOUT"
            evalue = "Timed out"
            formated_trace = []
        else:    
            rd_file = os.fdopen(rd)
            #std_file = os.fdopen(std_rd)
            etype, evalue, formated_trace = pickle.load(rd_file)
            stdout_stderr = std_file.read()
            std_file.close()
            rd_file.close()

        return (etype, evalue, formated_trace, stdout_stderr)
    else:
        # this is the child

        # the child doesn't need to read
        os.close(rd)
        os.close(std_rd)
        #FIXME redirect sys.stdout and sys.stderr to pipe

        try:
            #si = PipeSignalHandler(std_fd_wr, wr)
            #signal.signal(signum, si.cleanUp)
            
            os.dup2(std_wr, 1)
            os.dup2(std_wr, 2)
            code()
            os.close(std_wr)
            os.write(wr, pickle.dumps(("PASSED","Passed",[])))
        except Exception, e:
            os.close(std_wr)
            etype, evalue, etraceback = sys.exc_info()
            os.write(wr, pickle.dumps((etype, evalue, 
                    traceback.format_exception(etype, evalue, etraceback))))
        except:
            os.close(std_wr)
            estring, empty, etraceback = sys.exc_info()
            os.write(wr, pickle.dumps((empty, estring,
                    traceback.format_exception(estring, empty, etraceback))))
        
        os._exit(0)

######################################################################
# Start Param classes 
######################################################################
class Param(object):
    def __init__(self, name, type, default=None):
        self._name = name
        self._type = type
        if default is not None:
            self._default = self.castToType(default)
        else:
            self._default = default

    def getName(self):
        """Return the name of the parameter"""
        return self._name

    def getType(self):
        """Return the data type of the parameter"""
        return self._type

    def castToType(self, value):
        result = value
        try:
            if self._type == "integer":
                result = int(value)
            elif self._type == "string":
                if result[0] <> "'":
                    result = "%s" % value
            elif self._type == "eval":
                # hackish, but necessary for function test cases
                try:
                    result = eval(value)
                except NameError:
                    result = str(value)
                except TypeError:
                    pass
            elif self._type == "list":
                if type(value) != list:
                    if value is None:
                        result = []
                    elif type(value) == str or type(value) == unicode:
                        result = value.split(":")
                    else:
                        result = [value]
            elif self._type == "method":
                if type(value) == types.FunctionType or\
                                    type(value) == types.MethodType:
                    result = value
                else:
                    result = None
            else:
                #FIXME an error ?
                pass
        except ValueError:
            raise "ParamTypeError", "cannot cast %s as %s in %s parameter" %\
                  (value, self._type, self._name)

        return result

    def hasDefault(self):
        return self._default != None and self._default != [] 

    def getDefault(self):
        return self._default
            
class XMLParam(Param):
    """Represents a parameter

    A Param consists of a name and a data type and is used for defining
    parameters to TestSequences or TestCases.
    """
    def __init__(self, xml_element):
        type = xml_element.getAttribute("type")
        name = xml_element.getAttribute("name")
        if xml_element.hasAttribute("default"):        
            default = xml_element.getAttribute("default")
        else:
            default = None
        
        Param.__init__(self, name, type, default)

class ParamList(list):
    def __init__(self, data=None):
        self.pass_all_args = False
        if data is not None:
            #self.appendFunction(function):
            self.build(data)

    def build(self, data):
        raise AbstractMethod

    def processArgs(self, arg_dict):
        arguments = {}
        for param in self:
            param_name = param.getName()
            if not arg_dict.has_key(param_name):
                if param.hasDefault():
                    arguments[param_name] = param.getDefault()
                else:
                    raise MissingParameter, "Missing: %s" % (param_name)
            else:
                arguments[param_name] = \
                            param.castToType(arg_dict[param_name])

        if self.pass_all_args:
            for arg in arg_dict.keys():
                if not arguments.has_key(arg):
                    arguments[arg] = arg_dict[arg]

        return arguments

class XMLParamList(ParamList):
   def build(self, xml_element):
        param_elements = xml_element.getElementsByTagName("param")
        # FIXME ? if no param-list assuming pass all args
        if len(param_elements) == 0:
            self.pass_all_args = True

        for e in param_elements:
            self.append(XMLParam(e))

class FunctionParamList(ParamList):
    def build(self, function):
        argspec = inspect.getargspec(function)
        if argspec[2] or argspec[1]:
            # function takes variable arguments *args or **kwds
            self.pass_all_args = True
        
        if argspec[3]:
            firstDefaultedArg = len(argspec[0]) - len(argspec[3])
        else:
            firstDefaultedArg = -1

        for i in range(len(argspec[0])):
            if firstDefaultedArg != -1 and i >= firstDefaultedArg:
                self.append(Param(argspec[0][i], 'eval', 
                            default=repr(argspec[3][i-firstDefaultedArg])))
            else:
                self.append(Param(argspec[0][i], 'eval'))

######################################################################
# End Param classes 
######################################################################

######################################################################
# Start Source classes 
######################################################################

class Source(object):
    """Represents a block of source code"""

    def __init__(self, code, type):
        self._code = code
        self._type = type

    def getCode(self):
        """Return the source code text"""
        return self._code

    def getType(self):
        """Return the source code type"""
        return self._type


######################################################################
# End Source classes 
######################################################################

######################################################################
# Start SourceHandler classes
######################################################################

class EmptySourceHandler(SourceHandler):
    """Handler for Empty.

    It is assumed that an ini file actually has the test case results.
    """

    def __init__(self, name=None):
        SourceHandler.__init__(self)
        if name is None:
            self.name = "Empty"
        else:
            self.name = name

    def _setParamSrc(self):
        self.name = None
        self._param_list = ParamList()

    def _runInner(self):
        return (None, None, None, None) 

    def run(self, src, arg_dict={}, wait_before_kill=600):
        return self._runInner() 

    def getName(self, text=None):
        #if text is None:
        #    return self.name
        #else:
        return self.name 

class IniSourceHandler(SourceHandler):
    """Handler for ini files.

    It is assumed that an ini file actually has the test case results.
    """

    def _setParamSrc(self, file):
        self.name = os.path.basename(os.path.splitext(file))
        self._param_list = ParamList()
        config = ConfigParser.SafeConfigParser()
        config.read(file)

    def run(self, src, arg_dict={}, wait_before_kill=600):
        pass

    def getName(self, junk=None):
        return None
                    
class FunctionSourceHandler(SourceHandler):
    """Handler for python functions, based on PythonSourceHandler"""
    def _setParamSrc(self, module, function):
        self.module_name = module
        self.function_name = function

        #self._param_list = ParamList()
        self._mod = __import__(module)
        self._src = getattr(self._mod, function)
        try:
            self._param_list = FunctionParamList(self._src)
        except:
            self._param_list = FunctionParamList() 

    def _runInner(self):
        self._src(**self._arg_dict)
        
    def run(self, arg_dict={}, wait_before_kill=600):
        """Run the Python function"""
        self._arg_dict = arg_dict
        return runWithTimeout(self._runInner, wait_before_kill)
    
    def getName(self, junk=None):
        return "%s+%s" % (self.module_name, self.function_name)

class XMLSourceHandler(SourceHandler):
    def __init__(self, *args, **kwds):
        #self._source_factory = XMLSourceFactory()
        SourceHandler.__init__(self, *args, **kwds)

    def _setParamSrc(self, xml_element, filename, path):
        self.filename = filename
        self.path = path
            
        try:
            param_list_element = xml_element.getElementsByTagName("param-list")[0]
            self._param_list = XMLParamList(param_list_element)
        except IndexError:
            self._param_list = XMLParamList() 
        
        source_element = xml_element.getElementsByTagName("source")[0]
        source = source_element.firstChild.nodeValue
        type = source_element.getAttribute("type")
        self._src = Source(source, type)
        #self._src = self._source_factory.make(source_element)
        
    def getName(self, suite=None):
        if suite is None:
            return self.filename
        else:
            return "%s+%s" % (suite, self.filename)

class PythonSourceHandler(XMLSourceHandler):
    """Handler for python source. Refactored to use runWithTimeout
    """

    def _runInner(self):
        exec self._src.getCode().strip() in self._arg_dict

    def run(self, arg_dict={}, wait_before_kill=600):
        """Run the Python source"""
        #self._src = src
        self._arg_dict = arg_dict
        return runWithTimeout(self._runInner, wait_before_kill)
            
class ShellSourceHandler(XMLSourceHandler):
    """Handler for shell source."""

    def _runInner(self):
        status, output = commands.getstatusoutput("sh %s" % self._tmp_file.name)
        if status != 0:
            script_file_name = "failed-tc-%s-%s.sh" % (
                        os.path.splitext(os.path.basename(self.filename))[0],\
                        datetime.datetime.now().strftime("%H%M.%S"))
            shutil.copyfile(self._tmp_file.name, script_file_name)
            raise TestError, "status: %s, script: %s, stdout below:\n%s" % \
                (status, script_file_name, output)

        # return stdout & stderr to parent
        print output
        
    def run(self, arg_dict={}, wait_before_kill=600):
        """Run the shell script"""
        self._tmp_file = tempfile.NamedTemporaryFile()
        self._arg_dict = arg_dict
        for k in arg_dict.keys():
            if type(arg_dict[k]) == list:
                self._tmp_file.write("%s=\"%s\"\n" % (k, ":".join(arg_dict[k])))
            #elif self._type == "method":
            elif type(arg_dict[k]) == types.FunctionType or\
                                 type(arg_dict[k]) == types.MethodType:
                    pass
                    # FIXME raise error ? or figure some way to pass shell code.
            else:
                self._tmp_file.write("%s=\"%s\"\n" % (k, arg_dict[k]))

        self._tmp_file.write(self._src.getCode())
        self._tmp_file.flush()

        return runWithTimeout(self._runInner, wait_before_kill)

######################################################################
# End SourceHandler classes
######################################################################

######################################################################
# Start SourceHandlerReader class
######################################################################

#class SourceHandlerFactory(object):
class SourceHandlerReader(Reader):
    """Creates SourceHandler instances

    Maintains dictionaries of type->handler and type->setup block mappings.
    Creates SourceHandlers as appropriate using these dictionaries.
    """
    def __init__(self):
        Reader.__init__(self)

    def _registerFactories(self):
        self.registerFactory(XMLSourceHandlerFactory(ShellSourceHandler, "sh"))
        self.registerFactory(XMLSourceHandlerFactory(PythonSourceHandler, 
                                                                    "python"))
        self.registerFactory(XMLSourceHandlerFactory(FunctionSourceHandler))
        #FIXME function soure handler

class XMLSourceHandlerFactory(Factory):
    def __init__(self, handler_class, src_type=None):
        if src_type is None:
            self.key_var = ['module', 'function']
        elif type(src_type) == str:
            self.key_var = ['element','filename', 'path']
        else:
            raise TypeError, "type must be string, got: %s" % (src_type)
            
        self._src_type = src_type
        self._handler_class = handler_class
        Factory.__init__(self)
        
    def test(self, *args, **kwds):
        if self._src_type is None:
            values = self._parseArgs(*args, **kwds)
            if len(values) != len(self.key_var):
                return False

            (module, function) = values
            if type(module) is not str or type(function) is not str:
                return False

            try:
                __import__(module)
            except ImportError:
                return False

            return True
        else:
            values = self._parseArgs(*args, **kwds)
            if len(values) != len(self.key_var):
                return False

            element = values[0]
            try:
                source_element = element.getElementsByTagName("source")[0]
                src_type = source_element.getAttribute("type")
            except AttributeError, strerr:
                return False
            except IndexError, strerr:
                return False

            if src_type != self._src_type:
                return False

        return True 
        
    def make(self, *args, **kwds):
        """Return a SourceHandler object capable of processsing the specified source element"""
        if self._src_type is None:
            (module, function) = self._parseArgs(*args, **kwds)
            result = self._handler_class(module, function)
        else:
            (element, filename, path) = self._parseArgs(*args, **kwds)
            result = self._handler_class(element, filename, path)
        
        return result

