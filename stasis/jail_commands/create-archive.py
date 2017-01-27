
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

import stasis

def intro():
    """Create archive"""
    return ["Create archive from a partition on local machine."]

def abbreviation():
    """abbreviation at command line instead of full module name"""
    return "ca"

def setOptions(parser):
    """add module specific options for parsing command line"""
    parser.add_option("-a", "--archive-dir",
                      dest="archive_dir",
                      help="Archive destination directory")
    parser.add_option("-d", "--description",
                      help="Description of jail")
    parser.add_option("-j", "--jail",
                      help="Jail directory")

    parser.set_defaults(archive_dir=None)
    parser.set_defaults(description=None)
    parser.set_defaults(jail=None)

def runCommand(options, args, config_dict, stasis, logger):
    """run the command"""
    factory = stasis.JailFactory(logger)
    jail = factory.make(options.jail, options.description)
    jail.createArchive(options.archive_dir)
