#!/usr/bin/env python
# -------------------------------------------------------------------------- #
# Copyright 2011-2012, Indiana University                                    #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #
"""
Description: Dynamic provisioning tool in Teefaa. Installs customized images of Operating System on Bare Metal machine.  
"""
__author__ = 'Koji Tanaka'

import time
import subprocess
import ConfigParser
import optparse
import os
import logging
import logging.handlers

def setup_logger():
    #Setup logging
    logger = logging.getLogger("Teefaa_dynamicprovisioning")
    logger.setLevel(logging.DEBUG)    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler("/tmp/logfile.log")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False #Do not propagate to others
    
    return logger

def main():
    
    
    parser = optparse.OptionParser()
    #help is auto-generated
    parser.add_option("--host", dest="host", help="Host to provision")
    parser.add_option("--imagedir", dest="imagedir", help="Directory where image is.")
    parser.add_option("--overwritting", dest="overwritting", help="Directory with configuration files to overwrite the old ones.")
    parser.add_option("--ostype", dest="ostype", help="OS image type")
    parser.add_option("--defaultIf", dest="defaultIf", help="Default Network Interface")
    parser.add_option("--ipaddr", dest="ipaddr", help="IP address of the host to reinstall")
    parser.add_option("--gateway", dest="gateway", help="Gateway of the network.")
    parser.add_option("--netmask", dest="netmask", help="Network mask")
    parser.add_option("--dns", dest="dns", help="DNS server")
    parser.add_option("--partitioning", dest="partitioning", help="Partitions file")    
    parser.add_option("--prologue", dest="prologue", help="Script to execute before reinstall")
    parser.add_option("--epilogue", dest="epilogue", help="Script to execute after reinstall")
    
        
    (options, args) = parser.parse_args()
            
    DPHOST = options.host
    ImageDir = options.imagedir
    OverWriting = options.overwritting
    OsType = options.ostype
    Interface = options.defaultIf
    IpAddr = options.ipaddr
    Gateway = options.gateway
    NetMask = options.netmask
    DNS = options.dns
    Partitioning = options.partitioning
    Prologue = options.prologue
    Epilogue = options.epilogue
    
    RSYNC = "rsync -a -stat --one-file-system"

    log=setup_logger()

    # Partitioning
    CMD = "scp " + Partitioning + " partitioning.batch"
    log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    
    CMD = "fdisk /dev/sda < partitioning.batch"
    log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    
    # Make swap
    CMD = "mkswap /dev/sda1"
    log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    
    # Enable swap
    CMD = "swapon /dev/sda1"
    log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    
    if OsType == "ubuntu":
        # Make ext4 File System
        CMD = "mkfs.ext4 /dev/sda2"
        log.debug(CMD)    
    elif OsType == "rhel5":
        # Make ext3 File System
        CMD = "mkfs.ext3 /dev/sda2"
        log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    
    # Wait
    time.sleep(5)
    
    # Mount /dev/sda2
    CMD = "mount /dev/sda2 /mnt"
    log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    
    # Wait
    time.sleep(5)
    
    # Copy the image.
    CMD = RSYNC + " " + ImageDir + "/ " + "/mnt"
    log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    # copy common files
    CMD = RSYNC + " " + OverWriting + "/ " + "/mnt"
    log.debug(CMD)
    subprocess.check_call(CMD, shell=True)
    
    if OsType == "ubuntu":
        # Add Hostname and modify interface
        CMD = "echo " + DPHOST + " > /mnt/etc/hostname"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \" \" >> /mnt/etc/network/interfaces"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"auto " + Interface + "\" >> /mnt/etc/network/interfaces"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"iface " + Interface + " inet static\" >> /mnt/etc/network/interfaces"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"    address " + IpAddr + "\" >> /mnt/etc/network/interfaces"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"    netmask " + NetMask + "\" >> /mnt/etc/network/interfaces"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"    gateway " + Gateway + "\" >> /mnt/etc/network/interfaces"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"    dns-nameservers " + DNS + "\" >> /mnt/etc/network/interfaces"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        # Switch UUID
        FILE = "/boot/grub/grub.cfg"
        CMD1 = "grep \"search --no-floppy --fs-uuid --set=root\" " + "/mnt" + FILE + " |head -1| awk '{print $5}'"
        log.debug(CMD1)
        #OLDUUID = subprocess.check_output(CMD1, shell=True).rstrip()
        OLDUUID = subprocess.Popen(CMD1, stdout=subprocess.PIPE ,shell=True).communicate()[0].strip()
        CMD2 = "ls -la /dev/disk/by-uuid/ |grep sda2| awk '{print $9}'"
        log.debug(CMD2)
        #NEWUUID = subprocess.check_output(CMD2, shell=True).rstrip()
        NEWUUID = subprocess.Popen(CMD2, stdout=subprocess.PIPE ,shell=True).communicate()[0].strip()
        CMD = "sed -i -e \"s/" + OLDUUID + "/" + NEWUUID + "/\"" + " /mnt" + FILE
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
    elif OsType == "rhel5":
        # Add Hostname and modify Interface
        CMD = "echo HOSTNAME=" + DPHOST + " >> /mnt/etc/sysconfig/network"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"IPADDR=" + IpAddr + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"NETMASK=" + NetMask + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "echo \"GATEWAY=" + Gateway + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)    
    
    # Epilogue Script
    if not Epilogue == "none":
        CMD = "scp " + Epilogue + " " + "/root/epilogue"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "chmod u+x /root/epilogue"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "/root/epilogue"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
    
    # Grub Installation
    if OsType == "ubuntu":
        # mount devices
        CMD = "mount -t proc proc /mnt/proc"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "mount -t sysfs sys /mnt/sys"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "mount -o bind /dev /mnt/dev"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        time.sleep(5)
        CMD = "chroot /mnt grub-install /dev/sda"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        # Umount
        CMD = "umount /mnt/proc"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "umount /mnt/sys"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
        CMD = "umount /mnt/dev"
        log.debug(CMD)
        subprocess.check_call(CMD, shell=True)
    elif OsType == "rhel5":
        CMD = "grub-install --root-directory=/mnt /dev/sda"
        log.debug(CMD)
        subprocess.call(CMD, shell=True)
    
    # Wait
    time.sleep(5)
    # print Message.
        
if __name__ == "__main__":
    main()
