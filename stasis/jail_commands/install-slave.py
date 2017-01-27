
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
    """Load a jail into a partion"""
    return ["Format partition and expand slave archive file."]

def abbreviation():
    """abbreviation at command line instead of full module name"""
    return "in"

def setOptions(parser):
    """add module specific options for parsing command line"""
    parser.add_option("-a", "--archive-file",
                      dest="archive_file",
                      help="Specify the owner of the boot (required).")
    parser.add_option("-b", "--boot",
                      action="store_true",
                      help="Set system to boot from slave OS")
    parser.add_option("-e", "--extras",
                      action="append",
                      help="Specify the owner of the boot (required).")
    parser.add_option("-j", "--jail-dir",
                      dest="jail_dir",
                      help="Directory to install jail achive to.")
    parser.add_option("-u", "--user",
                      help="Specify the owner of the boot (required).")

    parser.set_defaults(archive_file=None)
    parser.set_defaults(boot=False)
    parser.set_defaults(extras=[])
    parser.set_defaults(jail_dir=None)
    parser.set_defaults(user=None)

def runCommand(options, args, conf_dict, stasis, logger):
    """run the command"""
    factory = stasis.ArchiveFactory(conf_dict['archive_paths'], logger)
    if options.jail_dir is not None:
        if options.archive_file is None and not options.boot:
            sterr = "No archive file specified and not setting boot"
            logger.error(sterr)
            raise stasis.JailException, sterr
        
        archive = factory.make(options.jail_dir, options.archive_file)
        if options.archive_file is not None:
            archive.install(options.extras)
        
        if options.boot:
            archive.setDefaultBoot()
            result = stasis.reboot()
            if result is not None:
                logger.error(result)
                raise stasis.JailException, "reboot failed: %s" % result    
    else:
        sterr = "No jail directory specified"
        logger.error(sterr)
        raise stasis.JailException, sterr
        
        

















#JAILS_PATH = "/jails"
#TARGET_PATH = "/jails/bootable"
#MOUNT_PATH = "/mnt"
#EXTRAS_PATH = "/jails/extras"


#def parse_options():
    ##
    ## parse the command line options
    ##
    #short_opts = "htmfbu:enxcld:"
    #long_opts = ["help","targets","mounts","force","boot","user=",
                 #"extras","nfs","pipeline-nfs","convenient","list",
                 #"description="]
    #opts, args = getopt(sys.argv[1:], short_opts, long_opts)
#
    #functions = []
    #options = []
    #for opt, value in opts:
        #if opt in ("-h","--help"):
            #functions = [usage]
            #break
        #elif opt in ("-l", "--list"):
            #functions = [list]
            #break
        #elif opt in ("-t", "--targets"):
            #functions = [list_targets]
            #break
        #elif opt in ("-m", "--mounts"):
            #functions = [list_mounts]
            #break
        #elif opt in ("-f", "--force"):
            #options.append("force")
        #elif opt in ("-b", "--boot"):
            #options.append("boot")
        #elif opt in ("-e","--extras"):
            #options.append("extras")
        #elif opt in ("-n","--nfs"):
            #options.append("nfs")
        #elif opt in ("-x","--pipeline-nfs"):
            #options.append("pipeline-nfs")
        #elif opt in ("-c","--convenient"):
            #options.append("extras")
            #options.append("nfs")
            #options.append("pipeline-nfs")
        #elif opt in ("-u","--user="):
            #options.append(("user", value))
        #elif opt in ("-d", "--description="):
            #options.append(("description", value))
#
    #return functions, options, args

def device_node(mountpt):
    ##
    ## find the device node from fstab from the mountpt
    ##
    master_fstab = open("/etc/fstab")
    for line in master_fstab:
        parts = line.split()
        if parts[1] == mountpt:
            return parts[0]
    return None

#def usage():
    ##
    ## show script usage information
    ##
    #print "Create and boot a slave partition with the specified target."
    #print "Usage: %s [options] <target> <mount point> <user-tag>" % sys.argv[0]
    #print "[options]"
    #print " -h, --help           Show this usage information."
    #print " -l, --list           List available partitions/distros."
    #print " -t, --targets        List available targets."
    #print " -m, --mounts         List available mount points."
    #print " -f, --force          Just do it.  No questions."
    #print " -b, --boot           Boot into the new slave."
    #print " -e, --extras         Install extra packages."
    #print " -n, --nfs            Mount nfs at /nfs."
    #print " -x, --pipeline-nfs   Mount pipeline nfs at /ximian-nfs."
    #print " -c, --convenient     Do convenience stuff. Equivalent to -enx."
    #print " -u, --user           Specify the owner of the boot (required)."
    #print " -d, --description    Indicate what the boot will be used for (encouraged)"


def list():
    ##
    ## list available slave parititions and the distros which are on them
    ##
    ### ret, output = getstatusoutput('cat /boot/grub/menu.lst | grep title | cut -d " " -f 2,3')
    ### if not ret:
    ###    print output
    ### else:
    ###    raise "ListError", output
    os.system("python /usr/bin/qa-slaves-query")


def list_targets():
    ##
    ## list the available bootable jails
    ##
    try:
        files = os.listdir(TARGET_PATH)
        found_target = 0
        if files:
            for f in files:
	        if f[-7:]==".tar.gz":
                    print f[:-7]
                    found_target = 1
        if not found_target:
            raise "TargetError", "No targets found"

    except OSError, e:
        raise "TargetError", e


def list_mounts():
    ##
    ## list the available mount points
    ##
    mounts = []
    try:
        dirs = os.listdir(MOUNT_PATH)
        for d in dirs:
            if os.path.isdir("%s/%s" %(MOUNT_PATH,d)):
                mounts.append(d)
                print d
        if not mounts:
            raise "MountError", "No mount points found"

    except OSError, e:
        raise "MountError", e

def create_tarball_path(target):
    tarball = "%s/%s.tar.gz" % (TARGET_PATH, target)
    return tarball

def unpack_target(target, mountpt):
    ##
    ## unpack the jail tarball to the specified location
    ##
    tarball = create_tarball_path(target)
    untar_cmd = "tar xzf %s" % (tarball)
    os.chdir("%s/%s" % (MOUNT_PATH, mountpt))
    ret, output = getstatusoutput(untar_cmd)
    if ret:
        raise "UnpackError", output


def config_grub(target, mountpt):
    ##
    ## configure grub to default boot to the specified partition; modify
    ## the menu to show the target for the partition
    ##
    ret, output = getstatusoutput("cp -f /boot/grub/menu.lst /boot/grub/menu.lst.old")
    if ret: 
        raise "GrubError", output

    linect = 0
    default_line = None
    new_menu = []
    entries = []
    grub_menu = open("/boot/grub/menu.lst.old")
    for line in grub_menu:
        if default_line == None:
            if line[:7] == "default":
                default_line = linect
        if line[:5] == "title":
            entry = line[5:-1].strip().split(" ")[0]
            entries.append(entry)
            if entry == mountpt:
                new_menu.append("title %s (%s)\n" % (entry,target))
            else:
                new_menu.append(line)
        else:
            new_menu.append(line)

        linect += 1
    grub_menu.close()

    if default_line == None:
        raise "GrubError", "Could not find default line in menu.lst"

    new_default = entries.index(mountpt)

    new_file = open("/boot/grub/menu.lst", 'w')
    for i in xrange(len(new_menu)):
        if i == default_line:
            new_file.write("default %s\n" % new_default)
        else:
            new_file.write(new_menu[i])
    new_file.close()
   
         
def config_fstab(mountpt):
    ##
    ## configure the fstab of the jail, mounting the master partition
    ## under /mnt/master
    ##
    slave_fstab = []
    master_fstab = open("/etc/fstab")
    master_device = device_node("/")
    if master_device == None:
        print ":-/ Could not find device for /mnt/master"
        sys.exit(1)

    for line in master_fstab:
        if line.find(master_device) > -1:
            slave_fstab.append("%s\t/mnt/master\text3\tdefaults\t1 1\n" % \
                               master_device)
        elif line.find("/mnt") > -1:
            if line.find(mountpt) > -1:
                slave_root = line.replace("%s/%s" % (MOUNT_PATH, mountpt), "/")
                slave_fstab.append(slave_root)
        else:
            slave_fstab.append(line)
    f = open("%s/%s/etc/fstab" % (MOUNT_PATH,mountpt),'w')
    for line in slave_fstab:
        f.write(line)
    f.close()


def write_jail_scripts(mountpt):
    ##
    ## put a qa-master script in the path of the jails which will
    ## qa-boot to the master
    ##
    qa_master = "%s/%s/usr/local/bin/qa-master" % (MOUNT_PATH,mountpt)
    f = open(qa_master, 'w')
    qa_master_script = """#!/bin/sh
if test -z $1 ; then
    chroot /mnt/master qa-boot -r master
    reboot &
else
    echo Reboot into the master partition
    echo Usage: qa-master
    echo '(takes zero arguments)'
    exit 0
fi
"""
    f.write(qa_master_script)
    f.close()
    os.chmod(qa_master, 755)


def write_etc_files(mountpt):

    ## copy the authorized_keys* files into the jail
    root_ssh_path = "%s/%s/root/.ssh" % (MOUNT_PATH,mountpt)
    auth_keys = "/root/.ssh/authorized_keys*"
    if os.path.exists(auth_keys):
        if not os.path.exists(root_ssh_path):
            os.mkdir(root_ssh_path)
        shutil.copy(auth_keys, root_ssh_path)

    ## copy the host keys into the jail
    etc_ssh_path = "%s/%s/etc/ssh" % (MOUNT_PATH,mountpt)
    for key in glob("/etc/ssh/*key*"):
        shutil.copy(key, etc_ssh_path)

    ## copy the resolv.conf file into the jail
    etc_path = os.path.join(MOUNT_PATH, mountpt, "etc")
    resolv_conf = "/etc/resolv.conf"
    shutil.copy(resolv_conf, etc_path)


def install_extras(target, mountpt):
    jail_path = os.path.join(MOUNT_PATH, mountpt)
    extras = os.path.join(EXTRAS_PATH, target)
    if os.path.exists(extras):
        jail_extras = os.path.join(jail_path, "root", "extras")
        if not os.path.exists(jail_extras):
            os.mkdir(jail_extras)
        for extra in glob(os.path.join(extras, "*")):
            shutil.copy2(extra, jail_extras)
    getstatusoutput("chroot %s rpm -Uvh /root/extras/*" % jail_path)


#def mount_nfs(mountpt):
    #jail_path = os.path.join(MOUNT_PATH, mountpt)
    #nfs_path = os.path.join(jail_path,"nfs")
    #if not os.path.exists(nfs_path):
        #os.mkdir(nfs_path)
    ##ret, output = getstatusoutput("chroot %s mount -t nfs dudley:/nfs /nfs" % jail_path)
    #if ret:
        #raise "MountError", output


#def mount_pipeline_nfs(mountpt):
    #jail_path = os.path.join(MOUNT_PATH, mountpt)
    #nfs_path = os.path.join(jail_path,"ximian-nfs")
    #if not os.path.exists(nfs_path):
        #os.mkdir(nfs_path)
    #ret, output = getstatusoutput("chroot %s mount -t nfs pipeline-nfs:/ximian /ximian-nfs" % jail_path)
    #if ret:
        #raise "MountError", output


def reboot(target):
    ##
    ## reboot the machine
    ##
    print ":-! Rebooting to %s..." % target
    getstatusoutput("reboot")

def serialize_usage(mountpt, distro, user, description):
    sys.stdout.write(":-o Serializing usage information... ")
    # MOUNT_PATH
    picklefile = "%s/usage.pickle" % JAILS_PATH
    picklefile_tmp = "%s.tmp" % picklefile
    try:
        f = open(picklefile, "r")
        status = pickle.load(f)
        f.close()
    except:
        print "hmmmm!", sys.exc_info()[0]
        status = {}
    
    data = { "distro": distro, "user": user, "description": description }
    status[mountpt] = data
    
    f = open(picklefile_tmp, "w")
    pickle.dump(status, f)
    f.close()
    os.rename(picklefile_tmp, picklefile)
    sys.stdout.write(":-)")    

    textfile = "%s/usage.txt" % JAILS_PATH
    textfile_tmp = "%s.tmp" % textfile
    mountpts = []
    for key, value in status.items():
        mountpts.append(key)
    mountpts.sort()
    f = open(textfile_tmp, "w")
    for i in mountpts:
        str =  "%s: %s, %s, %s" % (i, status[i]["distro"], status[i]["user"], status[i]["description"])
        f.write(str)
        f.write("\n")
    f.close()
    os.rename(textfile_tmp, textfile)
    print ":-)"

def main():

    has_user = 0
    try:
        functions, options, args = parse_options()

        description = "Unknown (next time use -d with qa-slave)"

        # Ew.  Surely there's a better way.
        for o in options:
            try:
                opt, a = o
                if opt == "user":
                    user = a
                    has_user = 1
                if opt == "description":
                    description = a
            except TypeError:
                pass
            except ValueError:
                pass
        
    except GetoptError, e:
        print ":-/ %s" % e
        sys.exit(1)

    for doit in functions:
        try:
            doit()
        except ("MountError", "TargetError"), e:
            print ":-/ %s" % e
    if functions:
       sys.exit(0)
    else:
        try:
            target, mountpt = args
            tarball = create_tarball_path(target)
            if os.path.exists(tarball) == False:
                print ":-/ Invalid target."
                print "Currently available targets are: "
                list_targets()
                sys.exit(1)
        except ValueError:
            tv_show = ["Romper Room","Sesame Street","Mr. Rogers",
                       "The Electric Company","Indiana", "Jerry Springer"]

            print "8=] You're so stupid you failed %s." % random.sample(tv_show,1)[0]
            usage()
            sys.exit(1)

        if has_user == 0:
            print "You must specify a username."
            print ""
            usage()
            sys.exit(1)


        sys.stdout.write(":-o Checking mount point... ")
        sys.stdout.flush()
        try:
            if os.listdir("%s/%s" % (MOUNT_PATH,mountpt)):
                if "force" in options:
                    print ":-p"
                    del_mount = "y"
                else:
                    del_mount = raw_input(":-/\n:-O Mount point not empty!  Do you want to delete the contents of %s/%s? [y/N] " % (MOUNT_PATH,mountpt))
                if del_mount.lower().strip() == "y":
                    print ":-o Deleting contents of %s/%s... " % \
                          (MOUNT_PATH,mountpt)

                    # rather than calling rm, just unmount, format and remount
                    # this is faster, and since we don't really care about 
                    # what's on the partition, totally safe
                    # - jyeo, 2004.08.16

                    #ret, output = getstatusoutput("rm -rf %s/%s/*" % (MOUNT_PATH,mountpt))

                    sys.stdout.write(":-o unmounting %s/%s... " % \
                                     (MOUNT_PATH,mountpt))
                    sys.stdout.flush()
                    ret, output = getstatusoutput("umount %s/%s" % (MOUNT_PATH,mountpt))
                    if ret:
                        print ":-/ Could not unmount partition. %s" % output
                        sys.exit(1)
                    else:
                        print ":-)"

                    # try to find the device node to format
                    sys.stdout.write(":-o finding device node for %s/%s... " % \
                                     (MOUNT_PATH,mountpt))
                    sys.stdout.flush()
                    device = device_node("%s/%s" % (MOUNT_PATH,mountpt))
                    if device == None:
                        print ":-/ Could not find device for %s" % mountpt
                        sys.exit(1)
                    else:
                        print ":-)"

                    sys.stdout.write(":-o running mkfs on %s... " % device)
                    sys.stdout.flush()
                    ret, output = getstatusoutput("mkfs.ext3 %s" % device)
                    if ret:
                        print ":-/ Could not format partition. %s" % output
                        sys.exit(1)
                    else:
                        print ":-)"

                    sys.stdout.write(":-o remounting %s on %s/%s... " % \
                                     (device,MOUNT_PATH,mountpt))
                    sys.stdout.flush()
                    ret, output = getstatusoutput("mount %s/%s" % (MOUNT_PATH,mountpt))
                    if ret:
                        print ":-/ Could not remount partition. %s" % output
                        sys.exit(1)
                    else:
                        print ":-)"
                else:
                    sys.exit(1)
            else:
                print ":-)"
        except OSError, e:
            print ":-/ Could not access mount point.  %s" % e
            sys.exit(1)

        try:        
            sys.stdout.write(":-o Extracting the tarball... ")
            sys.stdout.flush()
            unpack_target(target, mountpt)
            sys.stdout.write(":-)\n")
        except "UnpackError", e:
            print ":-/ Could not unpack target.  %s" % e
            sys.exit(1) 

        try:
            sys.stdout.write(":-o Editing the boot's motd... ")
            motd_path = "%s/%s/%s" % (MOUNT_PATH, mountpt, "etc/motd")
            os.remove(motd_path)
            motd_file = open(motd_path, "w")
            motd1 = "distro: %s\n" % target
            motd2 = "user: %s\n" % user
            motd3 = "description: %s\n" % description
	    motd4 = "date: %s\n" % time.strftime("%B %m, %Y %I:%M:%S %p %Z")
	    motd_separator = "*" * 30 + "\n"
	    motd_file.write(motd_separator)
	    motd_file.write("\n")
            motd_file.write(motd1)
            motd_file.write(motd2)
            motd_file.write(motd3)
	    motd_file.write(motd4)
	    motd_file.write("\n")
	    motd_file.write(motd_separator)
            motd_file.close()
            sys.stdout.write(":-)\n")

        except NameError, e: # Not sure which exceptions need to be caught here
            print ":-/ Unable to edit %s: %s" % (motd_path, e)
            sys.exit(1)

        serialize_usage("%s/%s" % (MOUNT_PATH, mountpt), target, user, description)
   
        try:
            sys.stdout.write(":-o Configuring grub to boot %s... " % mountpt)
            sys.stdout.flush()
            config_grub(target, mountpt)
            sys.stdout.write(":-)\n")
        except "GrubError", e:
            print ":-/ Could not configure grub. %s" % e
            sys.exit(1)

        try:
            sys.stdout.write(":-o Configuring %s's fstab... " % mountpt)
            sys.stdout.flush()
            config_fstab(mountpt)
            sys.stdout.write(":-)\n")
        except "FstabError", e:
            print ":-/ Could not configure slave fstab. %s " % e
            sys.exit(1)

        sys.stdout.write(":-o Writing jail utility scripts to %s... " % mountpt)
        sys.stdout.flush()
        write_jail_scripts(mountpt)
        sys.stdout.write(":-)\n")

        try:
            sys.stdout.write(":-o Writing etc files to %s... " % mountpt)
            sys.stdout.flush()
            write_etc_files(mountpt)
            sys.stdout.write(":-)\n")
        except "CopyError", e:
            ## non-fatal
            print ":-/ Couldn't copy key file.  %s" % e

        if "extras" in options:
            sys.stdout.write(":-o Installing extra packages to %s..." % mountpt)
            sys.stdout.flush()
            install_extras(target, mountpt)
            print ":-)"

        if "nfs" in options:
            try:
                sys.stdout.write(":-o Mounting nfs in %s..." % mountpt)
                sys.stdout.flush()
                #mount_nfs(mountpt)
                print ":-)"
            except "MountError", e:
                print ":-\ Could not mount nfs.  %s" % e

        if "pipeline-nfs" in options:
            try:
                sys.stdout.write(":-o Mounting pipeline nfs in %s..." % mountpt)
                sys.stdout.flush()
                #mount_pipeline_nfs(mountpt)
                print ":-)"
            except "MountError", e:
                print ":-/ Could not mount pipeline nfs.  %s" % e

        if "boot" in options:
            reboot(target)


            

if __name__ == "__main__":
    main()
