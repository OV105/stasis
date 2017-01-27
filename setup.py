
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
from distutils.core import setup
from distutils.command.bdist_rpm import bdist_rpm

NAME = 'stasis'

def getFiles(sub_dir):
    result = []
    path = os.path.join(os.curdir, sub_dir)
    list = os.listdir(path)
    for file in list:
        #ignore hidden files
        if file[0] == ".":
            continue
            
        #ignore directories 
        if os.path.isdir(os.path.join(path, file)):
            continue
            
        result.append(os.path.join(sub_dir, file))

    return result

def scripts():
    return getFiles('scripts')

def manFiles():
    return getFiles('doc/man')

def exampleFiles():
    return getFiles('test/examples')

def docFiles():
    return ["ToDo", "doc/Tutorial", "AUTHORS","COPYING","README"]

fd = open("%s_default.conf" % NAME, "w")
fd.write("[%s_default]\n" % NAME)
fd.write(os.path.join("search_paths=/usr/share", NAME))
fd.write("\n")
fd.close()
                

setup (
    name = NAME,
    version = '1.0',
    description = """Frame work for automating the execution of test cases.""",
    author = """Tim Lee <timlee@novell.com>""",
    author_email = 'timelee@novell.com',
    url = 'http://www.novell.com',
    packages = [NAME],
    scripts = scripts(),
    package_data = {NAME:['xsd/*.xsd','commands/*','jail_commands/*']},
    data_files = [
                 ("share/man/man1", manFiles()),
                 ("share/doc/packages/%s/examples" % (NAME), exampleFiles()),
                 ("share/doc/packages/%s" % (NAME), docFiles()),
                 ('/etc/%s' % NAME, ['%s_default.conf' % NAME])
                 ],
    cmdclass = {
                'bdist_rpm': bdist_rpm
              }
)

