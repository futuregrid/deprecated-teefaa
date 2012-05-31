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
import optparse
import os

parser = optparse.OptionParser()
parser.add_option('--host',dest="host",default=False)
parser.add_option('--conf',dest="conf",default="/opt/teefaa/etc/call_agent.conf")
parser.add_option('--recipe',dest="recipe",default=False)
options, remainder = parser.parse_args()

def help():
    print """
    usage:
    
      teefaa.py --host <HOSTNAME> --conf <CONFIG_FILE> --recipe <RECIPE_FILE>
    """
    
if (options.host == False) or (options.conf == False) or (options.recipe == False):
    help()
    exit()

config = ConfigParser.ConfigParser()
config.read(options.conf)

recipe = ConfigParser.ConfigParser()
recipe.read(options.recipe)

DPHOST = options.host
RECIPE = options.recipe
COMMAND = config.get("config","command")
MGMT = config.get("config","mgmt")
NETBOOT = config.get("config","netboot")
LOCALBOOT = config.get("config","localboot")
PXECONF = config.get("config", "pxelinux.cfg")
Interface = recipe.get("main","default-if")
IpAddr = recipe.get("default-if",DPHOST)
Gateway = recipe.get("main","default-gw")
NetMask = recipe.get("default-if","netmask")

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

# Copy command and recipe.
CMD = "scp " + COMMAND + " " + DPHOST + ":agent.py"
subprocess.check_call(CMD, shell=True)
CMD = "scp " + RECIPE + " " + DPHOST + ":recipe.txt"
subprocess.check_call(CMD, shell=True)

# Run agent.
CMD = "ssh " + DPHOST + " ./agent.py --host " + DPHOST + " --recipe recipe.txt" 
subprocess.check_call(CMD, shell=True)