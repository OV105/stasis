
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

import sys
import os
import shutil
import random
import pickle
import time

from getopt import getopt, GetoptError
from commands import getstatusoutput
from glob import glob


def intro():
    """List information about system"""
    return ["List information about system"]

def abbreviation():
    """abbreviation at command line instead of full module name"""
    return "ls"

def setOptions(parser):
    """add module specific options for parsing command line"""
    parser.add_option("-a", "--all",
                      action="store_true",
                      help="List all information about system")
    parser.add_option("-m", "--mounts",
                      action="store_true",
                      help="List available mount points")
    parser.add_option("-s", "--search",
                      help="Regular expression to search archives")

    parser.set_defaults(all=False)
    parser.set_defaults(mounts=False)
    parser.set_defaults(search=None)

def runCommand(options, args, conf_dict, stasis, logger):
    """run the command"""
    #result = [[],[]]
    if options.all:
        options.mounts = True
        options.search = ".*"

    if options.search is not None:
        factory = stasis.ArchiveFactory(conf_dict['archive_paths'], logger)
        if not options.terse:
            print "Available jails on this machine."

        if options.verbose == 1:
            for archive in factory.search(options.search):
                print " %s" % archive
        else:
            for archive in factory.findArchive(options.search):
                print " %s" % archive
    
    if options.all:
        print " "

    if options.mounts:
        if not options.terse:
            print "Available mount points on this machine."

        for mp in stasis.getMountPoints():
            print " %s" % mp







