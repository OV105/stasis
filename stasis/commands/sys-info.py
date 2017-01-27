
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

GROUP = "Information"

def intro():
    return ["Queries for system configuration information"]

def abbreviation():
    return "si"

def setOptions(parser, stasis):
    parser.add_option("-s", "--save",
                      help="File to save information to.")
    parser.add_option("-q", "--query",
                      action="store_true",
                      help="System to query")

    try:
        parser.remove_option("--console")
        parser.remove_option("--i18n")
        parser.remove_option("--test")
        parser.remove_option("--logfile")
    except ValueError:
        pass

    parser.set_defaults(save=None)
    parser.set_defaults(query=False)

def runCommand(util):
    factory = stasis.SysInfoFactory()
    si = factory.make()
    if options.save is not None:
        import cPickle
        fd = open(options.save, 'w')
        cPickle.dump(si, fd)
        fd.close()
    elif options.query:
        print si.getProp("kernel_release")

