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
Description: Symplified Dynamic Provisioning tool in Teefaa. Installs customized images of Operating System on Bare Metal machine.  
"""
__author__ = 'Koji Tanaka'

import time
import subprocess
import ConfigParser
import argparse
import os


parser = argparse.ArgumentParser(prog="teefaa", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="FutureGrid Teefaa Dynamic Provisioning Help ")
parser.add_argument('-H','--host',dest="host", required=True, metavar='hostname', help='Host that will be provisioned with a new OS.')
parser.add_argument('-C','--conf',dest="conf", metavar='config_file', default="/opt/teefaa/etc/teefaa.conf", help='Configuration file.')
parser.add_argument('-O','--os',dest="os", required=True, metavar='OS', help='Name of the OS image that will be provisioned.')
parser.add_argument('--site',dest="site", required=True, metavar='site_name', help='Name of the site.')

options = parser.parse_args()


config = ConfigParser.ConfigParser()
config.read(options.conf)

siteinfo = ConfigParser.ConfigParser()
siteinfo.read(options.site)

DPHOST = options.host
SITE = options.siteinfo
COMMAND = config.get("config","command")
MGMT = config.get("config","mgmt")
NETBOOT = config.get("config","netboot")
LOCALBOOT = config.get("config","localboot")
PXECONF = config.get("config", "pxelinux.cfg")
Interface = siteinfo.get("general","default-if")
IpAddr = siteinfo.get(Interface,DPHOST)
Gateway = siteinfo.get("general","default-gw")
NetMask = siteinfo.get(Interface,"netmask")

# Ready to netboot
CMD = "ssh " + MGMT + " cp " + PXECONF + "/" + NETBOOT + " " + PXECONF + "/" + DPHOST
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

# Copy command and siteinfo.
CMD = "scp " + COMMAND + " " + DPHOST + ":agent.py"
subprocess.check_call(CMD, shell=True)
CMD = "scp " + SITE + " " + DPHOST + ":" + options.site
subprocess.check_call(CMD, shell=True)

# Run agent.
CMD = "ssh " + DPHOST + " ./agent.py --host " + DPHOST + " --recipe " + options.site 
subprocess.check_call(CMD, shell=True)