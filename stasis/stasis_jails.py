
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
"""
stasis_jail module

Provides common jail classes for stasis
"""

import os
import re
import shutil
import sys
import logging 
import ConfigParser
import datetime
import tarfile
import commands
import time
import stat
import threading

CMD_TIMEOUT = 600
#DEFAULT_JAIL_CONF_DIR_LIST = ["/etc/jailtool", \
#                              os.path.expanduser("~/jailtool")]

ARCHIVE_EXTENSIONS = {'tar.gz':':gz', 'tgz':':gz', \
                      'tar.bz2':':bz2', 'bz2':':bz2'}
EXTENSION_PARTS = ['tar', 'gz', 'tgz', 'bz2']

   

def getExtension(filename):
    return ".".join(os.path.basename(filename).split("-")[-1].split('.')[1:])

def isValidExtension(filename):
    extn = getExtension(filename)
    return extn in ARCHIVE_EXTENSIONS.keys()

def parseFilename(filename):
    (distro,ver,arch,fs,rest) = os.path.basename(filename).split("-")
    desc = rest.split(".")[0]
    extn = ".".join(rest.split('.')[1:])
    return (distro,ver,arch,fs,desc,extn)

def getJailtoolConfig(config_files=[]):
    conf_dict = {'archive_paths':[os.getcwd(), os.path.expanduser("~")],\
                'arch':None, 'mount_root':'/mnt', 'distro':None, \
                'rpm_paths':[os.getcwd(), os.path.expanduser("~")]}
    
    config_files.extend(["/etc/jailtool.conf", \
                          os.path.expanduser("~/jailtool.conf")])

    for conf_file in config_files:
        if os.path.isfile(conf_file):
            p = ConfigParser.SafeConfigParser()
            p.read(conf_file)
            if not p.has_section('jailtool'):
                continue

            for key in conf_dict.keys():
                if p.has_option('jailtool', key):
                    if type(conf_dict[key]) == list:
                        conf_dict[key].extend(p.get('jailtool',key).split(':'))
                    else:
                        conf_dict[key] = p.get('jailtool', key)

    return conf_dict

def buildFileName(distro, ver, arch, filesystem, descr, extn):
    if not ARCHIVE_EXTENSIONS.has_key(extn):
        raise JailException, "%s not in list of distributions" % (distro)

    result = "%s-%s-%s-%s-%s.%s" % (distro, ver, arch, filesystem, \
                                    re.sub("\.|-| ", "_", descr), extn)
    if result.count("-") != 4:
        raise JailException, "Too many '-' in: %s" % (result)

    return result

def setJailProp(jail_dir, filename, re_string):
    prop_file = os.path.join(jail_dir, filename)
    if os.path.isfile(prop_file):
        lines = open(prop_file).readlines()
        for line in lines:
            m = re.search(re_string, line)
            if m:
                return m.group(1)

    return None

def checkMount(dir, logger):
    if os.path.ismount(dir):
        return True
    
    try:
        logger.info("trying to mount: %s" % dir)
        runCmd("mount %s" % (dir), logger)
    except JailException:
        logger.warning("failed to mount: %s" % dir)
        return False
    else:
        logger.info("mounted: %s" % dir)
        return True

def runCmd(cmd, logger, event=None):
    if event is None:
        event = threading.Event()

    run_cmd = RunCmd(logger, cmd, event)
    logger.info("Starting command: %s" % cmd)
    event.clear()
    run_cmd.start()
    try:
        event.wait(CMD_TIMEOUT)
    except AssertionError:
        logger.debug("Already finished: %s" % cmd)
    else:
        if run_cmd.isAlive():
            raise JailException, "Command timedout: %s" % (cmd)

    if run_cmd.status != 0:
        raise JailException, "Cmd failed: %s\n %s" % (cmd, run_cmd.out)
    else:
        logger.info("Cmd completed: %s\n %s" % (cmd, run_cmd.out))

    return None
            
def getMountPoints(fstab="/etc/fstab"):
    result = []
    lines = open(fstab).readlines()
    loop_re = re.compile("\S+\s+\S+\s+\S+\s+.*loop.*")
    nfs_re = re.compile("^\S:/\S")
    mount_re = re.compile("^/\S+\s+(/\S+)\s")
    for line in lines:
        if not nfs_re.search(line) and not loop_re.search(line):
            m = mount_re.search(line)
            if m:
                result.append(m.group(1))

    return result

def reboot():
    status, output = commands.getstatusoutput("shutdown -r now")
    if status != 0:
        return output
    else:
        return None

class JailException(Exception):
    __name__ = "JailException"
    pass

class AbstractMethod(JailException):
    __name__ = "AbstractMethon"
    pass

class MissingPath(JailException):
    __name__ = "MissingPath"
    pass

class RunCmd(threading.Thread):
    def __init__(self, logger, cmd, event):
        self.logger = logger
        self.cmd = cmd
        self.event = event
        self.status = None
        self.out = None
        threading.Thread.__init__(self)

    def run(self):
        self.logger.info("Starting command: %s" % (self.cmd))
        self.status, self.out = commands.getstatusoutput(self.cmd)
        self.event.set()
        if self.status != 0:
            self.logger.error("Command: %s,\n %s" % (self.cmd, self.out))
        else:
            self.logger.debug("Command succeeded: %s" % (self.cmd))

class JailFactory:
    def __init__(self, logger):
        self.logger = logger
    
    def make(self, jail_dir, description=None):
        if description is None:
            description = datetime.datetime.now().strftime("%b_%d_%H%M")
        
        for jc in JAIL_CLASSES:
            if setJailProp(jail_dir, jc.DETECT_FILE, jc.DETECT_RE):
                return jc(jail_dir, description, self.logger)

        raise JailException, "Could not find jail class for: %s" % (jail_dir)

class UnixJail:
    def __init__(self, jail_dir, description, logger, extension="tar.bz2"):
        self.jail_dir = jail_dir
        self.description = description
        self.logger = logger
        if not ARCHIVE_EXTENSIONS.has_key(extension):
            raise JailException, "Archive extension %s not recognized" % (extension)
        
        self.extn = extension
        self._setProperties()

    def _setProperties(self):
        self.hosts = 'etc/hosts'
        self.resolv_conf = 'etc/resolv.conf'
        self.sshd_config = 'etc/ssh/sshd_config'
        self.authorized_keys_dir = 'root/.ssh/authorized_keys2'
        self.authorized_keys_file = 'root/.ssh/authorized_keys'
        self.ssh_config = 'etc/ssh'
        self.boot_mnt_pt = None
        self.fstab = 'etc/fstab'
        self.user = os.getlogin()
        self.version = None
        self.distro = None
        self.arch = None
        self.filesystem = None

    def _setVersion(self):
        #self.version = "0"
        self.version = setJailProp(self.jail_dir, self.VERSION_FILE, \
                                   self.VERSION_RE)

    def _setArch(self):
        self.arch = setJailProp(self.jail_dir, self.ARCH_FILE, self.ARCH_RE)

    def _setFilesystem(self):
        self.filesystem = None
        #if os.path.ismount(self.jail_dir):
        if checkMount(self.jail_dir, self.logger):
            mounts = commands.getoutput("mount").split("\n")
            for mount in mounts:
                m = re.search("%s type ([^ ]*) " % (self.jail_dir), mount)
                if m:
                    self.filesystem = m.group(1)
        else:
            #FIXME raise error ?
            pass

    def createArchive(self, dest_dir):
        self._setVersion() 
        self._setArch()
        self._setFilesystem()
        archive_name = buildFileName(self.DISTRO_STRING, self.version, \
                                     self.arch, self.filesystem, \
                                     self.description, self.extn)
        old_pwd = os.getcwd()
        os.chdir(self.jail_dir)
        mode = "w%s" % (ARCHIVE_EXTENSIONS[self.extn])
        tar = tarfile.open(os.path.join(dest_dir, archive_name), mode=mode)
        for file in os.listdir("."):
            if os.access(file, os.R_OK):
                tar.add(file)

        tar.close()
        os.chdir(old_pwd)

    def configureMounts(self, source_fstab):
        lines = open(source_fstab).readlines()
        mount_points = []
        new_fstab = []
        root_mnt_options = None
        jail_boot_dev = None
        jail_fs_type = None
        root_re = re.compile("^(\S*)\s+/\s+(\S+)\s+(\S+)\s+1\s+1")
        jail_re = re.compile("^(\S*)\s+%s\s+(\S+)\s+(\S+)\s" % (self.jail_dir))
        boot_re = re.compile("^(\S*)\s+/boot\s(.*)")
        mnt_re = re.compile("^/\S*\s+/(\S*)\s")
        nfs_re = re.compile("^\S*:/\S*\s+(\S*)\s")
        for line in lines:
            #Find root parition
            m = root_re.search(line)
            if m:
                new_fstab.append("%s /mnt/master %s %s 0 0\n" % \
                                (m.group(1), m.group(2), m.group(3)))
                root_mnt_options = m.group(3)
                mount_points.append("mnt/master")
                continue

            m = jail_re.search(line)
            if m:
                jail_boot_dev = m.group(1)
                jail_fs_type = m.group(2)
                continue

            m = boot_re.search(line)
            if m:
                new_fstab.append("%s /mnt/boot %s\n", (m.group(1), m.group(2)))
                mount_points.append("mnt/boot")
                self.boot_mnt_pt = "/mnt"
                continue

            m = mnt_re.search(line)
            if m:
                mount_points.append(m.group(1))


            m = nfs_re.search(line)
            if m:
                mount_points.append(m.group(1))
                
            new_fstab.append(line)
        
        if root_mnt_options is None or jail_boot_dev is None:
            raise JailException, "could not process %s" % source_fstab
        else:
            new_fstab.insert(0, "%s / %s %s 1 1\n" % \
                            (jail_boot_dev, jail_fs_type, root_mnt_options))

        fo = open(os.path.join(self.jail_dir, self.fstab), 'w')
        for new_line in new_fstab:
            fo.write(new_line)

        fo.close()

        for mount_dir in mount_points:
            mount_point = os.path.join(self.jail_dir, mount_dir)
            if os.path.exists(mount_point):
                if not os.path.isdir(mount_point):
                    try:
                        os.unlink(mount_point)
                        os.mkdir(mount_point)
                    except OSError, err:
                        self.logger.error("Creating mount point:%s \n%s" %\
                                         (mount_point, err))
            else:
                try:
                    os.makedirs(mount_point)
                except OSError, err:
                    self.logger.error("Creating mount point:%s \n%s" %\
                                      (mount_point, err))

    def getJailBootfileBasePath(self, boot_partition=False):
        if self.boot_mnt_pt is not None:
            return self.boot_mnt_pt
        else:
            if boot_partition:
                return "/mnt/boot"
            else:
                return "/mnt/master/boot"

    def findAvailablePort(self, path):
        first_usable_port = '9000'
        try:
            dir = os.access(path, os.R_OK)
        except:
            self.logger.error('Could not read %s' % path)
            raise MissingPath, 'Could not read %s' % path

        dir = os.listdir(os.path.abspath(path))
        unavailable_ports = []
        for jail in dir:
            unavailable_ports.append(re.findall('.*-p(\d+)-.*', jail))

        unavailable_ports = filter(lambda l: l, unavailable_ports)
        unavailable_ports = map(lambda l: l[0], unavailable_ports)

        if len(unavailable_ports) == 1:
            return str(int(unavailable_ports[0]) + 1)
        elif len(unavailable_ports) > 1:
            greatest_port = reduce(lambda a,b: a > b and a or b, unavailable_ports)
            if greatest_port:
                return str (int(greatest_port) + 1)
            else:
                return first_usable_port
        else:
            return first_usable_port

    def findMachineIps(self):
        s = os.popen('/sbin/ifconfig','r').read()
        addr_re = re.compile('addr:(\d+\.\d+\.\d+\.\d+)')
        link_re = re.compile('([\w|:]+)\s+Link')
        links = link_re.findall(s)
        addrs = addr_re.findall(s)
        subnets = zip(links, addrs)
        is_user_ip = lambda (k,v): k.find(':') != -1
        subnets = filter(is_user_ip, subnets)
        filter_ip = lambda (k,v): v
        ips = map(filter_ip, subnets)
        ips.sort()
        return ips

    def findAvailableIp(self, path):
        try:
            dir = os.access(path, os.R_OK)
        except:
            self.logger.error('Could not read %s' % path)
            raise MissingPath, 'Could not read %s' % path

        dir = os.listdir(os.path.abspath(path))

        unavailable_ips = []

        for jail in dir:
            found = re.findall('.*-(\d+\.\d+\.\d+\.\d+)-.*', jail)
            if not found in unavailable_ips:
                unavailable_ips.append(found)
                

        unavailable_ips = map(lambda l: l[0], unavailable_ips)
        available_ips = findMachineIps()

        for ip in unavailable_ips:
            if ip in available_ips:
                available_ips.remove(ip)

        if len(available_ips) > 0:
            return available_ips[0]
        else:
            #print 'No more free IPs in this host'
            self.logger.error('No more free IPs in this host')
            return '0.0.0.0'

    def setSshdPortIP(self):
        jail_sshd_config = os.path.join(self.jail_dir, self.sshd_config)
        self.logger.info('Configuring ssh server file %s' % jail_sshd_config)
        if not os.access(jail_sshd_config, os.R_OK):
            self.logger.warning('Uable to read %s' % jail_sshd_config)
            return 1
        else:
            f = open(jail_sshd_config, 'r')
            config_file_text = f.read()
            f.close()
            
            config_file_text = re.sub('.Port.*|Port.*', 'Port %s' % self.port,\
                                       config_file_text)
            config_file_text = re.sub('.ListenAddress.*|ListenAddress.*', \
                                'ListenAddress %s' % self.ip, config_file_text)
            
            f = open(jail_sshd_config, 'w')
            f.write(config_file_text)
            f.close()
            
    def copyHostKeys(self):
        self.logger.info('Copying ssh host keys to jail')
        key_dir = os.path.join("/", self.authorized_keys_dir)
        if os.path.isdir(key_dir) and os.access(key_dir, os.R_OK):
            dest_key_dir = os.path.join(self.jail_dir, self.authorized_keys_dir)
            if os.path.exists(dest_key_dir):
                os.rename(dest_key_dir, "%s.%s" % (dest_key_dir,\
                          datetime.datetime.now().strftime("%b-%d-%y")))
            shutil.copytree(key_dir, dest_key_dir)

        key_file = os.path.join("/", self.authorized_keys_file)
        if os.access(key_file, os.R_OK):
            dest_key_file = os.path.join(self.jail_dir, self.authorized_keys_file)
            if os.path.exists(dest_key_file):
                os.rename(dest_key_file, "%s.%s" % (dest_key_file,\
                          datetime.datetime.now().strftime("%b-%d-%y")))
            shutil.copy(key_file, dest_key_file)

    def copyNetworkFiles(self):
        self.logger.info('Copying network files to jail')
        for file in [self.hosts, self.resolv_conf]:
            self.logger.info('Copying %s' % file)
            try:    
                shutil.copy(os.path.join("/", file),\
                            os.path.join(self.jail_dir, file))
            except:
                self.logger.warning('Unable to copy %s' % file)
            
    def setupPkgSystemOptions(self):
        raise AbstractMethod, "setupPkgSystemOptions" 

    def start_sshd(self):
        if re.search('redhat-62', self.target):
            self.command = '/usr/sbin/chroot %s /etc/rc.d/init.d/sshd start' % self.dir
            self.logger.info(os.popen(self.command).read())
        else:
            self.command = '/usr/sbin/chroot %s /etc/init.d/sshd start' % self.dir
            self.logger.info(os.popen(self.command).read())

class RedHatJail(UnixJail):
    DETECT_FILE = "etc/redhat-release"
    DETECT_RE = "(.*)"
    VER_FILE = DETECT_FILE
    VERSION_RE = "(.*)"
    ARCH_FILE = DETECT_FILE
    DISTRO_STRING = "RedHat"

class SuseJail(UnixJail):
    DETECT_FILE = "etc/SuSE-release"
    VERSION_FILE = DETECT_FILE
    ARCH_FILE = DETECT_FILE

class UbuntuJail(UnixJail):
    DETECT_FILE = "usr/share/doc/ubuntu-minimal"
    DETECT_RE = "(.*)"
    VER_FILE = DETECT_FILE
    VERSION_RE = "(.*)"
    ARCH_FILE = DETECT_FILE
    ARCH_RE = ".*"
    DISTRO_STRING = "Ubuntu"

class DebianJail(UnixJail):
    DETECT_FILE = "etc/debian_version"
    DETECT_RE = "(.*)"
    VER_FILE = DETECT_FILE
    VERSION_RE = "(.*)"
    ARCH_FILE = DETECT_FILE
    ARCH_RE = ".*"
    DISTRO_STRING = "Debian"

class GentooJail(UnixJail):
    DETECT_FILE = "etc/gentoo-release"
    DETECT_RE = "(.*)"
    VER_FILE = DETECT_FILE
    VERSION_RE = "(.*)"
    ARCH_FILE = DETECT_FILE
    ARCH_RE = ".*"
    DISTRO_STRING = "Gentoo"

class SlackwareJail(UnixJail):
    DETECT_FILE = "etc/slackware-version"
    DETECT_RE = "(.*)"
    VER_FILE = DETECT_FILE
    VERSION_RE = "(.*)"
    ARCH_FILE = DETECT_FILE
    ARCH_RE = ".*"
    DISTRO_STRING = "Slackware"

class OpenSUSEJail(SuseJail):
    DETECT_RE = "(openSUSE) "
    VERSION_RE = "openSUSE ([0-9\.]*) "
    ARCH_RE = "openSUSE .* \((.*)\)"
    DISTRO_STRING = "openSUSE"

class NLDJail(SuseJail):
    DETECT_RE = "(Novell Linux Desktop 9) "
    VERSION_RE = "Novell Linux Desktop (9) "
    ARCH_RE = "Novell Linux Desktop .* \((.*)\)"
    DISTRO_STRING = "NLD"

class SLEDJail(SuseJail):
    DETECT_RE = "(SUSE Linux Enterprise Desktop) "
    VERSION_RE = "SUSE Linux Enterprise Desktop ([0-9\.]*) "
    ARCH_RE = "SUSE Linux Enterprise Desktop .* \((.*)\)"
    DISTRO_STRING = "SLED"





class ArchiveFactory(object):
    def __init__(self, search_paths, logger=None, extrapkgs=[]):
        if logger is None:
            self.logger = logging.getLogger("jails")
            self.logger.setLevel(logging.ERROR)
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s\n")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            self.logger = logger

        self.search_paths = search_paths
        self.user = None
        self.ip = None
        self.port = None
        self.extrapkgs = extrapkgs
        self.archive_base = None
        self.jailpath_base = None

    def search(self, re_string=None):
        result = []
        archives = self.findArchive(re_string)
        for archive in archives:
            name = os.path.basename(archive)
            while name != '':
                name_part, ext = os.path.splitext(name)
                if not ext[1:] in EXTENSION_PARTS:
                    break

                name = name_part

            result.append(name)
        
        return result

    def findArchive(self, re_string):
        result = []
        if re_string is None:
            re_string = ".*"

        regexpr = re.compile(re_string)
        for dir in self.search_paths:
            try:
                filenames = os.listdir(dir)
            except OSError:
                continue

            for filename in filenames:
                file = os.path.join(dir, filename)
                if not os.path.isdir(file) and file[0] != '.' and \
                       os.access(file, os.R_OK):
                    m = regexpr.search(file)
                    if m:
                        if isValidExtension(file):
                            result.append(os.path.join(dir, file))

        return result
   
    def make(self, jail_path, re_string=None, extrapkgs=[]):
        """Make a archive object"""
        if re_string is None:
            archive = None
            fs = None
            distro = None
            extn = 'tgz'
        else:
            archive = self.findArchive(re_string)[0]
            (distro, ver, arch, fs, desc, extn) = parseFilename(archive)

        jailobj = None
        for jc in JAIL_CLASSES:
            if jc.DISTRO_STRING == distro:
                jailobj = jc(jail_path, desc, self.logger, extn)
                break

        return UnixArchive(archive, jail_path, jailobj, fs, \
                           ARCHIVE_EXTENSIONS[extn], self.logger)

    def list_archives(self, filter=None):
        if filter is None:
            filter = '*'

        return glob.glob(os.path.join(self.archive_base, filter))

class UnixArchive:
    def __init__ (self, archive, jailpath, jailobj, filesystem, mode, logger):
        self.archive = archive
        if jailpath is not None:
            self.dest = os.path.abspath(jailpath)
        else:
            self.dest = None 

        self.jailobj = jailobj
        self.logger = logger
        self.filesystem = filesystem
        self.mode = mode
        self.jail_dev = None
        self.master_dev = None
        self.boot_dev = None
        self.master_id = None
        self.jail_id = None
        self._setProperties()
        self._processBootconf()
   
    def __str__(self):
        s = "<UnixArchive - %s>" % os.path.basename(self.archive).split(".")[0]
        return s

    def _setProperties(self):
        self.fstab = "/etc/fstab"
        self.boot_conf_base = '/boot'
        self.boot_conf_file = 'grub/menu.lst'
        self.boot_conf_path = os.path.join(self.boot_conf_base,\
                                           self.boot_conf_file)
        self.bootloader = 'grub'
        self.jail_grub_id = None


    def _processBootconf(self):
        self._setDevices()
        if self.bootloader == 'grub':
            self._processsGrubConf()
        else:
            pass

    def _setDevices(self):
        lines = open(self.fstab).readlines()
        for line in lines:
            m = re.search("^(\S*)\s+%s\s" % self.dest, line)
            if m:
                self.jail_dev = m.group(1)
                continue
            
            m = re.search("^(\S*)\s+/\s", line)
            if m:
                self.master_dev = m.group(1)
                continue
            
            m = re.search("^(\S*)\s+%s\s" % self.boot_conf_base, line)
            if m:
                self.boot_dev = m.group(1)
                continue

        return None

    def _processsGrubConf(self):
        lines = open(self.boot_conf_path).readlines()
        title_count = 0
        linect = 0
        default_line = None

        for line in lines:
            if line[:5] == "title":
                title_count += 1
                self.logger.debug("Found title line, count: %d" % title_count)
            elif re.search("^\s*kernel\s", line):
                self.logger.debug("Found kernel line, count: %d" % title_count)
                m = re.search("\sroot=%s\s" % self.jail_dev, line)
                if m:
                    self.jail_id = title_count - 1
                else:
                    m = re.search("\sroot=%s\s" % self.master_dev, line)
                    if m and self.master_id is None:
                        self.master_id = title_count - 1

            linect += 1

    def install(self, extra_pkgs=[]):
        if self.archive is None:
            raise JailException, "Cannot install, no archive file specified"

        #if os.path.ismount(self.dest):
        if checkMount(self.dest, self.logger):
            self.logger.info("entering formatParition()")
            self.formatPartition()

        self.unpackArchive()


        #self.jailobj.setupPkgSystemOptions()
        self.jailobj.configureMounts(self.fstab)
        self.writeJailScripts()
        #if not os.path.ismount(self.dest):
        if not checkMount(self.dest, self.logger):
            #FIXME
            self.jailobj.setSshdPortIp()

            #self.start_sshd()
            #self.copy_network_files()
        
        self.jailobj.copyHostKeys()
        (distro,ver,arch,fs,desc,extn) = parseFilename(self.archive)
        id_file = open(os.path.join(self.dest,'qa-jail-id'), 'w')
        id_file.write(self.dest)
        for pkg in extra_pkgs:
            id_file.write ("\nw/ " + pkg)

        id_file.close()

    def formatPartition(self):
        device = None
        lines = open(os.path.join("/", self.fstab)).readlines()
        for line in lines:
            m = re.search("^(\S*)\s+%s\s" % (self.dest), line)
            if m:
                device = m.group(1)
        
        if device is None:
            raise JailException, "Could not find device in for: %s" % (self.dest)

        cmds = []
        cmds.append("umount %s" % (self.dest))
        cmds.append("/sbin/mkfs.%s %s" % (self.filesystem, device))
        cmds.append("mount %s" % (self.dest))
        for cmd in cmds:
            runCmd(cmd, self.logger)

    def configureChroot(self):
        pass

    def writeJailScripts(self):
        if self.bootloader == 'grub':
            self._writeGrubJailScript()

    def _writeGrubJailScript(self):
        ##
        ## put a qa-master script in the path of the jails which will
        ## qa-boot to the master
        ##
        shutil.copy(self.boot_conf_path, "%s.bak" % self.boot_conf_path)
        slave_boot_conf = os.path.join(self.jailobj.getJailBootfileBasePath(),\
                                       self.boot_conf_file)
        mode = stat.S_IEXEC|stat.S_IWRITE|stat.S_IREAD|stat.S_IRGRP|\
               stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH

        for name,cmd in [("boot-master","reboot &"), ("set-master-boot", "")]:
            script_file = os.path.join(self.dest, "usr", "local",\
                                    "bin", name)
            f = open(script_file, 'w')
            qa_master_script = """#!/bin/sh
if [ `id -u` -ne 0 ] ; then
    echo "You must be root to run this script"
    exit 1
fi

if test -z $1 ; then
    #chroot /mnt/master qa-boot -r master
    mv %s %s.bak
    sed -e 's/^default [0-9]*/default %d/' %s.bak > %s 
    %s 
else
    echo Reboot into the master partition
    echo Usage: qa-master
    echo '(takes zero arguments)'
    exit 0
fi
""" % (slave_boot_conf, slave_boot_conf, self.master_id, slave_boot_conf, \
       slave_boot_conf, cmd)

            f.write(qa_master_script)
            f.close()
            os.chmod(script_file, mode)

    def setDefaultBoot(self):
        if self.bootloader == 'grub':
            self._setDefaultBootGrub()
        else:
            raise JailException, "Unrecognized bootloader: %s" % self.bootloader

    def _setDefaultBootGrub(self):
        ##
        ## modify grub menu.lst to set the default to the specified slave
        ##
        if self.jail_id is None:
            raise JailException, "%s not found in %s" % (device, self.boot_conf_file)
        
        fi = open(self.boot_conf_path, 'r')
        lines = fi.readlines()
        fi.close()
        fo = open(self.boot_conf_path, 'w')
        for line in lines:
            if line[:7] == "default":
                fo.write("default %s\n" % self.jail_id)
            else:
                fo.write(line)

        fo.close()

    def setMasterBoot(self):
        if self.bootloader == 'grub':
            self._setMasterBootGrub()
        else:
            raise JailException, "Unrecognized bootloader: %s" % self.bootloader

    def _setMasterBootGrub(self):
        ##
        ## modify grub menu.lst to set the default to the specified slave
        ##
        fi = open(self.boot_conf_path, 'r')
        lines = fi.readlines()
        fi.close()
        fo = open(self.boot_conf_path, 'w')
        for line in lines:
            if line[:7] == "default":
                fo.write("default %s\n" % self.master_id)
            else:
                fo.write(line)

        fo.close()

    def install_package (self, package):
        package_path = os.path.abspath(package)
        if not os.path.isfile(package_path):
            print 'Not such file: %s' % package_path
            return
        package_file = os.path.split(package_path)[1]
        shutil.copy(package_path, self.dir)
        command = '/usr/sbin/chroot %s %s %s %s' %\
                  (self.dir, self.pkg_system,
                   self.install_options, package_file)
        print command
        print os.popen(command).read()

    def install_extras(self, extra_pkgs):
        extra_string = ""
        for pkg in extra_pkgs:
            if not os.path.isfile (pkg):
                print 'No such file: %s' % pkg
            else:
                shutil.copy (pkg, self.dir)
                extra_string = extra_string + ' ' + os.path.split (pkg)[1]
        if extra_string != "":
            command = '/usr/sbin/chroot %s %s %s %s' %\
                      (self.dir, self.pkg_system,
                       self.install_options, extra_string)

            print command
            print os.popen (command).read()

    def unpackArchive(self):
        if self.archive is None:
            raise JailException, "Cannot install, no archive file specified"

        if os.path.isfile(self.dest):
            raise JailException, "Destination %s is a file" % self.dest
        elif os.path.isdir(self.dest):
            if not os.access(self.dest, os.W_OK):
                raise JailException, "Cannot write to %s" % self.dest
        else:
            try:
                self.logger.info('Making directory %s' % self.dest)
                os.makedirs(self.dest)
            except Exception, err:
                strerr = 'Unable to create %s\n %s' % (self.dest, err)
                self.logger.critical(strerr)
                raise JailException, strerr

        if os.access(self.archive, os.R_OK):
            old_dir = os.getcwd()
            os.chdir(self.dest)
            self.logger.info('Extracting: %s to %s' % (self.archive,self.dest))
            mode = "r%s" % (ARCHIVE_EXTENSIONS[getExtension(self.archive)])
            #os.popen('tar -zxvf %s' % self.archive).read()
            tar = tarfile.open(self.archive, mode)
            for member in tar.getmembers():
                tar.extract(member)

            tar.close()
            os.chdir(old_dir)
        else:
            strerr = 'Cannot read archive: %' % self.archive
            self.logger.critical(strerr)
            raise JailException, strerr

JAIL_CLASSES = [RedHatJail, UbuntuJail, DebianJail, GentooJail, SlackwareJail,\
                OpenSUSEJail, NLDJail, SLEDJail]
