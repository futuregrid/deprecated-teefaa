#!/usr/bin/env python
# -------------------------------------------------------------------------- #
# Copyright 2010-2011, Indiana University                                    #
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
parser.add_option('-H','--host',dest="host",default=False)
parser.add_option('-C','--conf',dest="conf",default=False)
parser.add_option('-O','--os',dest="os",default=False)
parser.add_option('--cluster',dest="cluster",default=False)
options, remainder = parser.parse_args()

def help():
    print """
    usage:
    
      dynamic_provisioning.py -H[--host] <HOSTNAME> -C[--conf] <CONFIG_FILE> --os <OS_TYPE> --cluster <CLUSTER_NAME>
    """
    
if (options.host == False) or (options.conf == False) or (options.os == False):
    help()
    exit()

config = ConfigParser.ConfigParser()
config.read(options.conf)

DPHOST = options.host
ImageDir = config.get(options.os,"rootimg")
ConfDir = config.get(options.os,"setting")
OsType = config.get(options.os,"ostype")
Agent = config.get(options.os,"agent")
Interface = config.get(options.cluster,"interface")
IpAddr = config.get("nodes",DPHOST)
Gateway = config.get(options.cluster,"gw")
NetMask = config.get(options.cluster,"netmask")
DNS = config.get(options.cluster,"nameservers")
MGMT = config.get(options.cluster,"mgmt")
PartitionBatch = ConfDir + "/partitioning.batch"
RSYNC = "rsync -av"
Epilogue = config.get(options.os,"epilogue")

# Ready to netboot
CMD = "ssh " + MGMT + " cp /tftpboot/pxelinux.cfg/" + Agent + " /tftpboot/pxelinux.cfg/" + DPHOST
subprocess.check_call(CMD, shell=True)
# Reboot the machine
CMD = "ssh " + MGMT + " rpower " + DPHOST + " boot"
# This will be changed to below soon.
#CMD = "ssh " + MGMT + " ipmitool -I lanplus chassis power on -U $USERNAME -P $SECRETPASS -H $BMCNAME"
subprocess.check_call(CMD, shell=True)

p = 1
while (not p == 0):
    CMD = "ssh " + MGMT + " \'ssh  -o \"ConnectTimeout 5\" " + DPHOST + " " + "hostname\' > /dev/null 2>&1" 
    p = subprocess.call(CMD, shell=True)
    if not p == 0:
        print ""
        print DPHOST ,"is booting and not ready yet..."
        print ""
        #exit()
        time.sleep(5)

# Switch it back to local boot
CMD = "ssh " + MGMT + " cp /tftpboot/pxelinux.cfg/localboot /tftpboot/pxelinux.cfg/" + DPHOST
subprocess.check_call(CMD, shell=True)


# Setup Interface
CMD = "ssh " + MGMT + " ssh " + DPHOST + " ifconfig " + Interface +  " " + IpAddr + " netmask " + NetMask
subprocess.check_call(CMD, shell=True)

# Setup routing
CMD = "ssh " + MGMT + " ssh " + DPHOST + " route add default gw " + Gateway
subprocess.check_call(CMD, shell=True)

# Partitioning
CMD = "ssh " + DPHOST + " fdisk /dev/sda < " + PartitionBatch
subprocess.check_call(CMD, shell=True)

# Make swap
CMD = "ssh " + DPHOST + " mkswap /dev/sda1"
subprocess.check_call(CMD, shell=True)

# Enable swap
CMD = "ssh " + DPHOST + " swapon /dev/sda1"
subprocess.check_call(CMD, shell=True)

if OsType == "ubuntu":
    # Make ext4 File System
    CMD = "ssh " + DPHOST + " mkfs.ext4 /dev/sda2"
    subprocess.check_call(CMD, shell=True)
elif OsType == "rhel5":
    # Make ext3 File System
    CMD = "ssh " + DPHOST + " mkfs.ext3 /dev/sda2"
    subprocess.check_call(CMD, shell=True)

# Wait
time.sleep(5)

# Mount /dev/sda2
CMD = "ssh " + DPHOST + " mount /dev/sda2 /mnt"
subprocess.check_call(CMD, shell=True)

# Wait
time.sleep(5)

# Copy the image.
CMD = RSYNC + " " + ImageDir + "/ " + DPHOST + ":/mnt"
subprocess.check_call(CMD, shell=True)
# copy common files
CMD = "rsync -av " + ConfDir + "/etc/ " + DPHOST + ":/mnt/etc"
subprocess.check_call(CMD, shell=True)

if OsType == "ubuntu":
    # Add Hostname and modify interface
    CMD = "ssh " + DPHOST + " \"echo " + DPHOST + " > /mnt/etc/hostname\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \" \" >> /mnt/etc/network/interfaces\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"auto " + Interface + "\" >> /mnt/etc/network/interfaces\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"iface " + Interface + " inet static\" >> /mnt/etc/network/interfaces\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"    address " + IpAddr + "\" >> /mnt/etc/network/interfaces\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"    netmask " + NetMask + "\" >> /mnt/etc/network/interfaces\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"    gateway " + Gateway + "\" >> /mnt/etc/network/interfaces\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"    dns-nameservers " + DNS + "\" >> /mnt/etc/network/interfaces\""
    subprocess.check_call(CMD, shell=True)
    # Switch UUID
    FILE = "/boot/grub/grub.cfg"
    CMD1 = "grep \"search --no-floppy --fs-uuid --set=root\" " + ImageDir + FILE + " |head -1| awk '{print $5}'"
    OLDUUID = subprocess.check_output(CMD1, shell=True).rstrip()
    CMD2 = "ssh " + DPHOST + " " + "ls -la /dev/disk/by-uuid/ |grep sda2| awk '{print $9}'"
    NEWUUID = subprocess.check_output(CMD2, shell=True).rstrip()
    CMD = "ssh " + DPHOST + " sed -i -e \"s/" + OLDUUID + "/" + NEWUUID + "/\"" + " /mnt" + FILE
    subprocess.check_call(CMD, shell=True)
elif OsType == "rhel5":
    # Add Hostname and modify Interface
    CMD = "ssh " + DPHOST + " \"echo HOSTNAME=" + DPHOST + " >> /mnt/etc/sysconfig/network\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"IPADDR=" + IpAddr + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface + "\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"NETMASK=" + NetMask + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface + "\""
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " \"echo \"GATEWAY=" + Gateway + "\" >> /mnt/etc/sysconfig/network-scripts/ifcfg-" + Interface + "\""
    subprocess.check_call(CMD, shell=True)    

# Epilogue Script
if not Epilogue == "none":
    CMD = "scp " + Epilogue + " " + DPHOST + ":/root/epilogue"
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " chmod u+x /root/epilogue"
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " /root/epilogue"
    subprocess.check_call(CMD, shell=True)

# Grub Installation
if OsType == "ubuntu":
    # mount devices
    CMD = "ssh " + DPHOST + " mount -t proc proc /mnt/proc"
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " mount -t sysfs sys /mnt/sys"
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " mount -o bind /dev /mnt/dev"
    subprocess.check_call(CMD, shell=True)
    time.sleep(5)
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " chroot /mnt grub-install /dev/sda"
    subprocess.check_call(CMD, shell=True)
    # Umount
    CMD = "ssh " + DPHOST + " umount /mnt/proc"
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " umount /mnt/sys"
    subprocess.check_call(CMD, shell=True)
    CMD = "ssh " + DPHOST + " umount /mnt/dev"
    subprocess.check_call(CMD, shell=True)
elif OsType == "rhel5":
    CMD = "ssh " + DPHOST + " grub-install --root-directory=/mnt /dev/sda"
    subprocess.call(CMD, shell=True)

# wait
time.sleep(5)
# Reboot the machine
CMD = "ssh " + DPHOST + " reboot"
subprocess.check_call(CMD, shell=True)
print "Fnishing dynamic provisioning... " + DPHOST + " is rebooting now:-)"
