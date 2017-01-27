
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
from stasis_exceptions import *
import os
import types
import datetime
import tarfile
import string

def expandArchive(archive_file_name, search_paths):
    found_archive = False
    for path in search_paths:
        archive_file = os.path.join(path, archive_file_name)
        if os.path.isfile(archive_file):
            found_archive = True
            break

    if found_archive:
        archive_dir = expandArchiveFile(archive_file)
    else:
        raise StasisException("Cannot find archive file: %s, in:\n %s" % (
                                archive_file_name, search_paths))

    return archive_dir

def findArchiveDirList(archive_file, today=True, dir=""):
    if today:
        search_string = os.path.join(dir, "stasis_%s_%s*" % (\
               string.split(os.path.basename(archive_file), '.')[0],\
               datetime.datetime.now().strftime( "%b-%d")))
    else:
        search_string = os.path.join(dir, "stasis_%s*" % (\
               string.split(os.path.basename(archive_file), '.')[0]))
   
    result = glob.glob(search_string)
    return result

def expandArchiveFile(archive_file):
    archive_dir = "stasis_%s_%s" % (\
                    string.split(os.path.basename(archive_file), '.')[0],\
                    datetime.datetime.now().strftime( "%b-%d-%H%M.%S" ))
    try:
        os.mkdir(archive_dir)
    except OSError, e:
        raise StasisException("Cannot create directory:\n %s\n %s" % (
                                        archive_dir, e.__str__()))
    
    #FIXME add support for zip files
    ext = os.path.splitext(archive_file)[1]
    if ext == ".bz2":
        mode = 'r:bz2'
    else:
        mode = 'r:gz'

    try:
        tar = tarfile.open(archive_file, mode)
        for item in tar:
            tar.extract(item, path=archive_dir)
    except Exception, e:
        raise StasisException("Error with archive file:\n %s\n %s" % (
                                archive_file, e.strerror))
    
    return archive_dir 

def runInDir(run_dir, callback):
    if not os.path.isdir(run_dir):
        raise StasisException("No run directory: %s" % (run_dir))
    
    if type(callback) != types.MethodType: 
        if type(callback) != types.FunctionType:
            raise StasisException("callback not method or function, got: %s" % \
                                  (type(callback)))

    old_cwd = os.getcwd()
    try:
        os.chdir(run_dir)
    except OSError, strerr:
        raise StasisException("Cannot open directory: %s, error: %s" % \
                               (run_dir, strerr))
    try:
        callback()
    except:
        os.chdir(old_cwd)
        raise

    os.chdir(old_cwd)

def addReporters(series, logdir, verbose, console, reporters=[]):
    #time_stamp = datetime.datetime.now().strftime("%b-%d-%H%M.%S")
    time_stamp = datetime.datetime.now().strftime("%b-%d-%H%M.%S")
    logfile = os.path.join(logdir, "run-%s.log" % (time_stamp))
    if os.path.isfile(logfile):
        time_stamp = "%s-a" % time_stamp

    picklefile = os.path.join(logdir, "run-%s.pickle" % (time_stamp))
    log_reporter = LogTestCaseReporter(verbose, logfile)
    pickle_reporter = PickleReporter(picklefile)
    series.addReporter(log_reporter)
    series.addReporter(pickle_reporter)
    if type(reporters) is list:
        for reporter in reporters:
            series.addReporter(reporter)
    else:
        series.addReporter(reporters)
        
    if console:
        console = ConsoleTestCaseReporter(verbose)
        series.addReporter(console)
    
    series.conf_file = os.path.join(logdir, "run-%s.conf" % (time_stamp))

def getStasisLibs(xsd_dir, suite_list, config_files):
    case_validator = XMLValidator(os.path.join(xsd_dir, "test-case.xsd"))
    case_lib = TestCaseLibrary(case_validator, suite_list)
    for conf_file in config_files:
        case_lib.addConfFile(conf_file)

    seq_validator = XMLValidator(os.path.join(xsd_dir, "test-sequence.xsd"))
    sequence_lib = TestSequenceLibrary(case_lib, suite_list)
    for conf_file in config_files:
        sequence_lib.addConfFile(conf_file)

    return (case_lib, sequence_lib)

def runSeries(series, arg_list, cycle, register_list=[], role=None):
    arg_dict = getArgDict(arg_list)
    rr = stasis.RoleRegistry(role=role)
    for reg in register_list:
        if os.path.isfile(reg):
            for reg in [r.strip() for r in open(reg).readlines()]:
                rr.addRole(reg.split("="))
        else:
            rr.addRole(reg.split("="))

    for i in range(cycle):
        dispatcher = RunDispatcher(series)
        dispatcher.run(arg_dict)
        file = series.saveConfFile()
        if file != series.conf_file:
            pass

def getArgDict(arg_list):
    arg_dict = {}
    for arg in arg_list:
        (name, value) = arg.split("=")
        arg_dict[unicode(name)] = unicode(value)
    return arg_dict

