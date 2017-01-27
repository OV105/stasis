
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
def testopia_case_pass_func():
    print "TESTOPIA_CASE_PASS_FUNC"

def test_case_func_archive():
    print "CASE_ARCHIVE"
    if not os.path.isfile("root_file"):
        raise "No root_file file"

    if not os.path.isdir("first_dir"):
        raise "No first_dir directory"

    if not os.path.isfile(os.path.join("first_dir","first_file")):
        raise "No first_dir/first_file file"
