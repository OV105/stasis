
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
import getpass
import time
import datetime
import stasis

#def setup(archive_file_name, _search_paths, _run_callback):
def setup(**kwds):
    #base_tc_name = kwds["_base_test_case_name"]
    function_name = kwds["_function_name"]
    if function_name == "test_case_func_archive":
        #fd = open("/tmp/logging", 'w')
        run_dir = stasis.expandArchive(kwds["archive_file_name"], 
                                       kwds["_search_paths"])
        stasis.runInDir(run_dir, kwds["_run_callback"])
        #fd.write("run_dir: %s\n" % run_dir)
        #old_cwd = os.getcwd()
        #os.chdir(run_dir)
        #callback = kwds["_run_callback"]
        #callback()
        #os.chdir(old_cwd)
        #fd.write("end\n")
        #fd.close()

def teardown(**kwds):
    pass

def test_case_pass_func():
    print "CASE_PASS_FUNC"

def test_case_func_archive():
    if not os.path.isfile("root_file"):
        raise "No root_file file in: %s" % (os.getcwd())
    print "Found: root_file"

    if not os.path.isdir("first_dir"):
        raise "No first_dir directory in: %s" % (os.getcwd())
    print "Found: first_dir"

    if not os.path.isfile(os.path.join("first_dir","first_file")):
        raise "No first_dir/first_file file in: %s" % (os.getcwd())
    print "Found: first_dir/first_file"

def background_process():
    print "BACKGROUND_PROCESS"
    back_file = "/tmp/stasis-background-%s-%s" %(getpass.getuser(),\
                     datetime.datetime.now().strftime("%b-%d"))
    fore_file = "/tmp/stasis-foreground-%s-%s" %(getpass.getuser(),\
                     datetime.datetime.now().strftime("%b-%d"))
    fd = open(back_file, 'w')
    fd.write("background started")
    fd.close()
    end_time = time.time() + 300
    found_fore = False
    while time.time() < end_time:
        if os.path.exists(fore_file):
            found_fore = True 
            print "Found foreground file: %s" % fore_file
            break
        time.sleep(2)

    #os.unlink(back_file)
    if not found_fore:
        raise "No foreground file found: %s" % fore_file
    else:
        #os.unlink(fore_file)
        pass

def foreground_process():
    print "FOREGROUND_PROCESS"
    back_file = "/tmp/stasis-background-%s-%s" %(getpass.getuser(),\
                     datetime.datetime.now().strftime("%b-%d"))
    fore_file = "/tmp/stasis-foreground-%s-%s" %(getpass.getuser(),\
                     datetime.datetime.now().strftime("%b-%d"))
    fd = open(fore_file, 'w')
    fd.write("foreground process")
    fd.close()
    found_back = False
    if os.path.exists(back_file):
        print "Found background file: %s" % back_file
        found_back = True 

    if not found_back:
        raise "No background file found: %s" % back_file

def foreground_process_2():
    print "FOREGROUND_PROCESS_2"
