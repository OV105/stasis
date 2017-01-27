
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
import shutil
import sys
import pdb
import glob

def setup_files():
    stasis_path = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    stasis_home = os.path.expanduser("~/stasis")
    if not os.path.exists(stasis_home):
        os.mkdir(stasis_home)
        os.mkdir(os.path.join(stasis_home, "conf"))

    test_dir = os.path.join(stasis_home, "unittest")

    if not os.path.exists(test_dir):
        os.mkdir(test_dir)

    conf_file = os.path.join(stasis_home, "conf", "unittest.conf")
    if not os.path.exists(conf_file):    
        conf_text = "[stasis_unittest]\n_version=1\n_search_paths="
        conf_text += "%s:%s:%s:%s\n"  % (test_dir,
                              os.path.join(test_dir, "unittest_xml_files"),
                              os.path.join(test_dir, "unittest_module_files"),
                              os.path.join(test_dir, "unittest_ini_files"))
        conf_text += "_module_paths=%s\n" % (
                              os.path.join(test_dir, "unittest_module_files")) 
        conf_text += "conf_arg_1=value 1\nconf_arg_2=value 2\n"
        conf_text += "\n[live_integration]\n_version=2\n_search_paths="
        conf_text += "%s\n" % (os.path.join(test_dir, 
                              "unittest_xml_files","live"))
        conf_text += "_module_paths=%s\n" % (
                    os.path.join(test_dir, "unittest_module_files")) 
        conf_text += "\n[stasis_examples]\n_search_paths="
        conf_text += "%s\n"  % (os.path.join(test_dir, "examples"))
        conf_text += "_module_paths=%s\n\n" % (
                                os.path.join(test_dir, "examples")) 
        fd = open(conf_file, 'w')
        fd.write(conf_text)
        fd.close()

    #for file in ["unittest_ini_files", "unittest_xml_files", "unittest_module_files"]:
    for file in glob.glob('*'):
        dest_path = os.path.join(test_dir, file)
        source_path = os.path.join(stasis_path, "test", file)
        if os.path.isdir(source_path):
            if not os.path.isdir(dest_path):
                shutil.copytree(source_path, dest_path)

def setup_path():
    stasis_path = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if sys.path.count(stasis_path) == 0:
        sys.path.append(stasis_path)

    env_old_path = os.environ["PATH"]
    script_path = os.path.join(stasis_path, "scripts")
    if env_old_path.count(script_path) == 0:
        env_new_path = "%s:%s" % (env_old_path, script_path)
        os.environ.update({"PATH":env_new_path})

    return env_old_path

