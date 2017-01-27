
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

def intro():
    """Set default boot partion"""
    return ["Set default boot partition and optionally reboot."]

def abbreviation():
    """abbreviation at command line instead of full module name"""
    return "bc"

def setOptions(parser):
    """add module specific options for parsing command line"""
    parser.add_option("-b", "--boot",
                      action="store_true",
                      help="Reboot system.")
    parser.add_option("-j", "--jail-dir",
                      dest="jail_dir",
                      help="Mount point to set as default boot partition")
    parser.add_option("-m", "--master",
                      action="store_true",
                      help="Set current (master) patition as default for boot.")

    parser.set_defaults(boot=False)
    parser.set_defaults(jail_dir=None)
    parser.set_defaults(master=False)

def runCommand(options, args, conf_dict, stasis, logger):
    """run the command"""
    factory = stasis.ArchiveFactory(conf_dict['archive_paths'], logger)
    archive = factory.make(options.jail_dir, None)
    result = ""
    if options.jail_dir is None:
        if options.master:
            archive.setMasterBoot()
            result = "Set boot to current partition."
        else:
            raise stasis.JailException, "Must set master or jail-dir option"
    else:
        archive.setDefaultBoot()
        result = "Set boot to partition: %s" % options.jail_dir
    
    if options.boot:
        result = stasis.reboot()
        if result is not None:
            logger.error(result)
            raise stasis.JailException, "reboot failed: %s" % result    

    return result
