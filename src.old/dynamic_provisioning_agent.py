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

parser = optparse.OptionParser()
parser.add_option('--host',dest="host",default=False)
parser.add_option('--recipe',dest="recipe",default=False)
options, remainder = parser.parse_args()

def help():
    print """
    usage:
    
      dynamic_provisioning_agent.py --host <HOSTNAME> --recipe <RECIPE_LIST>
    """
    
if (options.host == False) or (options.recipe == False):
    help()
    exit()

recipe = ConfigParser.ConfigParser()
recipe.read(options.recipe)

DPHOST = options.host
ImageDir = recipe.get("main","rootimg")
OverWriting = recipe.get("main","overwriting")
OsType = recipe.get("main","ostype")
Interface = recipe.get("main","default-if")
IpAddr = recipe.get("default-if",DPHOST)
Gateway = recipe.get("main","default-gw")
NetMask = recipe.get("default-if","netmask")
DNS = recipe.get("main","nameservers")
Partitioning = recipe.get("main","partitioning")
RSYNC = "rsync -av --one-file-system"
Prologue = recipe.get("main","prologue")
Epilogue = recipe.get("main","epilogue")

# Partitioning
CMD = "scp " + Partitioning + " partitioning.batch"
subprocess.check_call(CMD, shell=True)
CMD = "fdisk /dev/sda < partitioning.batch"
subprocess.check_call(CMD, shell=True)

# Make swap
CMD = "mkswap /dev/sda1"
subprocess.check_call(CMD, shell=True)

# Enable swap
CMD = "swapon /dev/sda1"
subprocess.check_call(CMD, shell=True)

if OsType == "ubuntu":
   # Make ext4 File System
   CMD = "mkfs.ext4 /dev/sda2"
   subprocess.check_call(CMD, shell=True)
elif OsType == "rhel5":
   # Make ext3 File System
   CMD = "mkfs.ext3 /dev/sda2"
   subprocess.check_call(CMD, shell=True)

# Wait
time.sleep(5)

# Mount /dev/sda2
CMD = "mount /dev/sda2 /mnt"
subprocess.check_call(CMD, shell=True)

# Wait
time.sleep(5)

# Copy the image.
CMD = RSYNC + " " + ImageDir + "/ " + "/mnt"
subprocess.check_call(CMD, shell=True)
# copy common files
CMD = RSYNC + " " + OverWriting + "/ " + "/mnt"
subprocess.check_call(CMD, shell=True)

if OsType == "ubuntu":
    # Add Hostname and modify interface
    CMD = "echo " + DPHOST + " > /mnt/etc/hostname"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \" \" >> /mnt/etc/network/interfaces"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"auto " + Interface + "\" >> /mnt/etc/network/interfaces"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"iface " + Interface + " inet static\" >> /mnt/etc/network/interfaces"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"    address " + IpAddr + "\" >> /mnt/etc/network/interfaces"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"    netmask " + NetMask + "\" >> /mnt/etc/network/interfaces"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"    gateway " + Gateway + "\" >> /mnt/etc/network/interfaces"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"    dns-nameservers " + DNS + "\" >> /mnt/etc/network/interfaces"
    subprocess.check_call(CMD, shell=True)
    # Switch UUID
    FILE = "/boot/grub/grub.cfg"
    CMD1 = "grep \"search --no-floppy --fs-uuid --set=root\" " + "/mnt" + FILE + " |head -1| awk '{print $5}'"
    #OLDUUID = subprocess.check_output(CMD1, shell=True).rstrip()
    OLDUUID = subprocess.Popen(CMD1, stdout=subprocess.PIPE ,shell=True).communicate()[0].rstrip()
    CMD2 = "ls -la /dev/disk/by-uuid/ |grep sda2| awk '{print $9}'"
    #NEWUUID = subprocess.check_output(CMD2, shell=True).rstrip()
    NEWUUID = subprocess.Popen(CMD2, stdout=subprocess.PIPE ,shell=True).communicate()[0].rstrip()
    CMD = "sed -i -e \"s/" + OLDUUID + "/" + NEWUUID + "/\"" + " /mnt" + FILE
    subprocess.check_call(CMD, shell=True)
elif OsType == "rhel5":
    # Add Hostname and modify Interface
    CMD = "echo HOSTNAME=" + DPHOST + " >> /mnt/etc/sysconfig/network"
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"IPADDR=" + IpAddr + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"NETMASK=" + NetMask + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface
    subprocess.check_call(CMD, shell=True)
    CMD = "echo \"GATEWAY=" + Gateway + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface
    subprocess.check_call(CMD, shell=True)    

# Epilogue Script
if not Epilogue == "none":
    CMD = "scp " + Epilogue + " " + "/root/epilogue"
    subprocess.check_call(CMD, shell=True)
    CMD = "chmod u+x /root/epilogue"
    subprocess.check_call(CMD, shell=True)
    CMD = "/root/epilogue"
    subprocess.check_call(CMD, shell=True)

# Grub Installation
if OsType == "ubuntu":
    # mount devices
    CMD = "mount -t proc proc /mnt/proc"
    subprocess.check_call(CMD, shell=True)
    CMD = "mount -t sysfs sys /mnt/sys"
    subprocess.check_call(CMD, shell=True)
    CMD = "mount -o bind /dev /mnt/dev"
    subprocess.check_call(CMD, shell=True)
    time.sleep(5)
    CMD = "chroot /mnt grub-install /dev/sda"
    subprocess.check_call(CMD, shell=True)
    # Umount
    CMD = "umount /mnt/proc"
    subprocess.check_call(CMD, shell=True)
    CMD = "umount /mnt/sys"
    subprocess.check_call(CMD, shell=True)
    CMD = "umount /mnt/dev"
    subprocess.check_call(CMD, shell=True)
elif OsType == "rhel5":
    CMD = "grub-install --root-directory=/mnt /dev/sda"
    subprocess.call(CMD, shell=True)

# Wait
time.sleep(5)
# print Message.
print ""
print "Fnishing dynamic provisioning... " + DPHOST + " is rebooting now:-)"
print ""
# Reboot the machine
CMD = "reboot"
subprocess.check_call(CMD, shell=True)
