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
Description: Simplified Dynamic Provisioning tool in Teefaa. Installs customized images of Operating System on Bare Metal machine.  
"""
__author__ = 'Koji Tanaka, Javier Diaz'

import time
import subprocess
import ConfigParser
import argparse
import os
import logging
import logging.handlers
import sys
import string
import time
import re

defaultconfigfile = "fg-server.conf"

class Teefaa():
    def __init__(self, config=None, verbose=False):        
        
        #general configuration
        self.verbose = verbose   
        self.configfile = None   
        self.logFilename = None
        self.logLevel = None
        self.command = None
        self.logDir = None
        self.logger = None
        self.generalconfig = None  #general config parser
        
        #set config file                
        if config != None:
            self.configfile = config
        else:
            self.setDefaultConfigFile()
        
        #log file
        self._logLevel_default = "DEBUG"
        self._logType = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        self.generalconfig = self.loadGeneralConfig()
        self.logger = self.setup_logger()
        
        self.logger.debug("\nTeefaa Reading Configuration file from " + self.configfile + "\n")
        
    
    def setDefaultConfigFile(self):
        '''
        Set the default configuration file when not configuration file is provided.
        This is always interactive because is executed when we create the object.'''
        
        localpath = "~/.fg/"
        self.configfile = os.path.expanduser(localpath) + "/" + defaultconfigfile
        if not os.path.isfile(self.configfile):
            self.configfile = "/etc/futuregrid/" + defaultconfigfile
            
            if not os.path.isfile(self.configfile):
                print "ERROR: teefaa configuration file " + self.configfile + " not found"
                sys.exit(1)
                 
    
    def setup_logger(self):
        #Setup logging
        logger = logging.getLogger("Teefaa")
        logger.setLevel(self.logLevel)    
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(self.logFilename)
        handler.setLevel(self.logLevel)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False #Do not propagate to others
        
        return logger
    
    def loadGeneralConfig(self):
        '''This loads the configuration that does not change.        
        This is always interactive because is executed when we create the object.'''
    
        config = ConfigParser.ConfigParser()
        config.read(self.configfile)
        
        section = 'Teefaa'        
        try:
            self.logFilename = os.path.expanduser(config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            print "No log option found in section " + section + " file " + self.configfile
            sys.exit(1)
        except ConfigParser.NoSectionError:
            print "Error: no section " + section + " found in the " + self.configfile + " config file"
            sys.exit(1)
        try:
            tempLevel = string.upper(config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            print "Warning: Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default
            tempLevel = self._logLevel_default
        self.logLevel = eval("logging." + tempLevel)
        try:
            self.command = config.get(section, 'command', 0)
            self.command = os.path.expanduser(os.path.dirname(__file__)) + "/" + self.command
            if not os.path.isfile(self.command):
                print "command file " + self.command + " not found."
                sys.exit(1) 
        except ConfigParser.NoOptionError:
            print "No command option found in section " + section + " file " + self.configfile
            sys.exit(1)
        try:
            self.logDir = os.path.expanduser(config.get(section, 'log_dir', 0))
        except ConfigParser.NoOptionError:
            print "No log_dir option found in section " + section + " file " + self.configfile
            sys.exit(1)
            
        return config
    
    def errorMsg(self, msg):
        self.logger.error(msg)
        if self.verbose:
            print msg
    
    def listImages(self, site):
        section = 'Teefaa-' + site.lower() + '-config'
        try:
            siteconfigfile = os.path.expandvars(os.path.expanduser(self.generalconfig.get(section, 'siteconf', 0)))
            if not os.path.isfile(siteconfigfile):
                self.errorMsg("The configuration file " + siteconfigfile + " does not exists. Section " + section)
                return
        except ConfigParser.NoOptionError:
            self.errorMsg("No siteconf option found in section " + section + " file " + self.configfile)
            return 
        except ConfigParser.NoSectionError:
            self.errorMsg("Error: no section " + section + " found in the " + self.configfile + " config file")            
            return
        #Networking Site information.
        siteinfo = ConfigParser.ConfigParser()
        siteinfo.read(siteconfigfile)
        
        images=[]
        for i in self._config.sections():
            if re.search("^Image",i.lower()):
                images.append(i.split("-")[1])
        return images
          
    def loadSpecificConfig(self, host, operatingsystem, site):
        '''This load the configuration of the site, machine and image to provision.
        Returns None or a dictionary.
        '''
        info = {}
        
        #Site PXE configuration
        section = 'Teefaa-' + site.lower() + '-config'       
        
        try:
            info['mgmt'] = self.generalconfig.get(section, 'mgmt', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No mgmt option found in section " + section + " file " + self.configfile)
            return 
        except ConfigParser.NoSectionError:
            self.errorMsg("Error: no section " + section + " found in the " + self.configfile + " config file")            
            return 
        try:
            info['pxeconf'] = self.generalconfig.get(section, 'pxelinux.cfg', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No pxelinux.cfg option found in section " + section + " file " + self.configfile)
            return 
        try:
            info['netboot'] = self.generalconfig.get(section, 'netboot', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No netboot option found in section " + section + " file " + self.configfile)
            return 
        try:
            info['localboot'] = self.generalconfig.get(section, 'localboot', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No localboot option found in section " + section + " file " + self.configfile)
            return 
        try:
            siteconfigfile = os.path.expandvars(os.path.expanduser(self.generalconfig.get(section, 'siteconf', 0)))
            if not os.path.isfile(siteconfigfile):
                self.errorMsg("The configuration file " + siteconfigfile + " does not exists. Section " + section)
                return
        except ConfigParser.NoOptionError:
            self.errorMsg("No siteconf option found in section " + section + " file " + self.configfile)
            return 
        
        #Networking Site information.
        siteinfo = ConfigParser.ConfigParser()
        siteinfo.read(siteconfigfile)
        
        section = 'General'
        try:
            info['default-if'] = siteinfo.get(section, 'default-if', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No default-if option found in section " + section + " file " + siteconfigfile)
            return 
        except ConfigParser.NoSectionError:
            self.errorMsg("Error: no section " + section + " found in the " + siteconfigfile + " config file")
            return
        try:
            info['default-gw'] = siteinfo.get(section, 'default-gw', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No default-gw option found in section " + section + " file " + siteconfigfile)
            return
        try:
            info['if2'] = siteinfo.get(section, 'if2', 0)
        except ConfigParser.NoOptionError:
            pass #optional for now
            #self.errorMsg("No if2 option found in section " + section + " file " + siteconfigfile)
            #return
        try:
            info['if3'] = siteinfo.get(section, 'if3', 0)
        except ConfigParser.NoOptionError:
            pass # optional for now
            #self.errorMsg("No if3 option found in section " + section + " file " + siteconfigfile)
            #return
        try:
            info['nameservers'] = siteinfo.get(section, 'nameservers', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No nameservers option found in section " + section + " file " + siteconfigfile)
            return
        
        try: #IP OF THE MACHINE TO PROVISION
            info['IpAddr'] = siteinfo.get(info['default-if'], host, 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No " + host + " option found in section " + info['default-if'] + " file " + siteconfigfile)
            return
        except ConfigParser.NoSectionError:
            self.errorMsg("Error: no section " + section + " found in the " + siteconfigfile + " config file")
            return 
        try: #NETMASK
            info['netmask'] = siteinfo.get(info['default-if'], 'netmask', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No netmask option found in section " + info['default-if'] + " file " + siteconfigfile)
            return
        
        
        #OS Image information        
        section = 'Image-' + operatingsystem.lower()
        try: 
            info['rootimg'] = siteinfo.get(section, 'rootimg', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No rootimg option found in section " + section + " file " + siteconfigfile)
            return
        except ConfigParser.NoSectionError:
            self.errorMsg("Error: no section " + section + " found in the " + siteconfigfile + " config file")
            return
        try: 
            info['overwriting'] = siteinfo.get(section, 'overwriting', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No overwriting option found in section " + section + " file " + siteconfigfile)
            return
        try: 
            info['partitioning'] = siteinfo.get(section, 'partitioning', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No partitioning option found in section " + section + " file " + siteconfigfile)
            return
        try: 
            info['ostype'] = siteinfo.get(section, 'ostype', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No ostype option found in section " + section + " file " + siteconfigfile)
            return
        try: 
            info['prologue'] = siteinfo.get(section, 'prologue', 0)
        except ConfigParser.NoOptionError:
            pass #optional for now
            #self.errorMsg("No prologue option found in section " + section + " file " + siteconfigfile)
            #return
        try: 
            info['epilogue'] = siteinfo.get(section, 'epilogue', 0)
        except ConfigParser.NoOptionError:
            pass#optional for now
            #self.errorMsg("No epilogue option found in section " + section + " file " + siteconfigfile)
            #return
        
        return info
    
    def provision(self, host, operatingsystem, site):

        info = self.loadSpecificConfig(host, operatingsystem, site)

        #Test begin
        #print " Provisioning " + host + " with OS, which is part of the " + operatingsystem + " site " + site
        #print str(info)
        #return 'OK'
        #Test end
    

        if info != None:
            try:
                # Ready to netboot
                CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " cp " + info['pxeconf'] + "/" + info['netboot'] + " " + info['pxeconf'] + "/" + host
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                if self.verbose:                    
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Coping the pxeboot netboot configuration. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Coping the pxeboot netboot configuration. cmd= " + CMD
                self.logger.error(msg)
                return msg
            
            try:   
                # Reboot the machine
                CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " rpower " + host + " boot"
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                # This will be changed to below soon.
                #CMD = "ssh " + info['mgmt'] + " ipmitool -I lanplus chassis power on -U $USERNAME -P $SECRETPASS -H $BMCNAME"
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Rebooting the machine. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Rebooting the machine. cmd= " + CMD 
                self.logger.error(msg)
                return msg
            
            #TODO: Prevent to wait forever.
            self.logger.debug(host + " is booting and not ready yet...")
            CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " \'ssh -q -oBatchMode=yes -o \"ConnectTimeout 5\" " + host + " " + "hostname\' > /dev/null 2>&1"
            CMD = "sudo " + CMD
            self.logger.debug(CMD)
            p = 1
            while (not p == 0):                 
                p = subprocess.call(CMD, shell=True)
                if not p == 0:
                    if self.verbose:
                        print ""
                        print host + " is booting and not ready yet..."
                        print ""
                    #exit()
                    time.sleep(5)
            self.logger.debug(host + " has started with the auxiliary netboot image.")
            
            try:            
                # Switch it back to local boot
                CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " cp /tftpboot/pxelinux.cfg/localboot /tftpboot/pxelinux.cfg/" + host
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Copying the pxeboot localdisk configuration. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Copying the pxeboot localdisk configuration. cmd= " + CMD
                self.logger.error(msg)
                return msg
            
            try:
                # Setup Default Interface
                CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " ssh " + host + " ifconfig " + info['default-if'] + " " + info['IpAddr'] + " netmask " + info['netmask']
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                if self.verbose:              
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Setting up the default interface. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Setting up the default interface. cmd= " + CMD
                self.logger.error(msg)
                return msg
            try:
                # Delete Default gw if it have
                CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " ssh " + host + " route delete default"
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "WARNING: Defailt Gateway doesn't exist. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
            except subprocess.CalledProcessError:
                msg = "ERROR: Deleting old default gateways information. cmd= " + CMD + ". sysexit= " + str(sys.exc_info())
                self.logger.error(msg)
                return msg
            try:
                # Setup routing
                CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " ssh " + host + " route add default gw " + info['default-gw']
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Setting up the Routing information. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Setting up the Routing information. cmd= " + CMD + ". sysexit= " + str(sys.exc_info())
                self.logger.error(msg)
                return msg
            try:
                # Copy command and siteinfo.
                CMD = "scp -oBatchMode=yes " + self.command + " " + host + ":agent.py"
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Sending the script to the machine. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Sending the script to the machine. cmd= " + CMD + ". sysexit= " + str(sys.exc_info())
                self.logger.error(msg)
                return msg
            try:
                # Run agent.
                CMD = "ssh -oBatchMode=yes " + host + " ./agent.py --host " + host + " --imagedir " + info['rootimg'] + \
                        " --overwritting " + info['overwriting'] + " --ostype " + info['ostype'] + \
                        " --defaultIf " + info['default-if'] + \
                        " --ipaddr " + info['IpAddr'] + " --gateway " + info['default-gw'] + \
                        " --netmask " + info['netmask'] + " --dns " + info['nameservers'] + \
                        " --partitioning " + info['partitioning']
                CMD = "sudo " + CMD
                #CHECK if prologue and epilogue exists
                if 'prologue' in info:
                    CMD += " --prologue " + info['prologue']
                if 'epilogue' in info: 
                    CMD += " --epilogue " + info['epilogue']
                self.logger.debug(CMD)    
                if self.verbose:                
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Reinstalling the machine. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Reinstalling the machine. cmd= " + CMD + ". sysexit= " + str(sys.exc_info())
                self.logger.error(msg)
                return msg
            
            try:
                # Get the log file.
                t = time.localtime()
                timestamp = str(t.tm_year) + "-" + str(t.tm_mon) + "-" + str(t.tm_mday) + "_" + str(t.tm_hour) + str(t.tm_min)  
                CMD = "scp -oBatchMode=yes " + host + ":/tmp/logfile.log " + self.logDir + "/provision-" + host + "." + timestamp
                CMD = "sudo " + CMD
                self.logger.debug(CMD) 
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Getting the log file. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        #return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Sending the script to the machine. cmd= " + CMD + ". sysexit= " + str(sys.exc_info())
                self.logger.error(msg)
                #return msg
            
            try:
                # Reboot machine
                CMD = "ssh -oBatchMode=yes " + info['mgmt'] + " ssh " + host + " reboot"
                CMD = "sudo " + CMD
                self.logger.debug(CMD)
                if self.verbose:
                    print ""
                    print "Fnishing dynamic provisioning... " + host + " is rebooting now:-)"
                    print ""
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Setting up the Routing information. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Setting up the Routing information. cmd= " + CMD + ". sysexit= " + str(sys.exc_info())
                self.logger.error(msg)
                return msg
            
            return 'OK'
            
        else:
            msg = "ERROR: Reading configuration for host " + host + ", site " + site + ", os " + operatingsystem
            self.logger.error(msg)
            return msg
        
            
            
def main():
    parser = argparse.ArgumentParser(prog="teefaa", formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="FutureGrid Teefaa Dynamic Provisioning Help ")
    
    subparsers = parser.add_subparsers(dest='subparser_name', help='Positional arguments group different options that can be' 
                                       ' displayed by specifying <positional_argument> -h')
    
    subparser_provision = subparsers.add_parser('provision', help='Functionality to provision a machine with an OS.')
    subparser_provision.add_argument('-H', '--host', dest="host", required=True, metavar='hostname', help='Host that will be provisioned with a new OS.')
    subparser_provision.add_argument('-C', '--conf', dest="conf", metavar='config_file', default="/opt/teefaa/etc/teefaa.conf", help='Configuration file.')
    subparser_provision.add_argument('-O', '--os', dest="os", required=True, metavar='OS', help='Name of the OS image that will be provisioned.')
    subparser_provision.add_argument('--site', dest="site", required=True, metavar='site_name', help='Name of the site.')
    
    subparser_info = subparsers.add_parser('info', help='Consult Information of teefaa')
    subparser_info.add_argument('-l', '--listimages', dest="images", metavar='site', help='List of images available for a site.')
    
    options = parser.parse_args()    
    
    if (options.subparser_name == 'provision'):
        conf = os.path.expandvars(os.path.expanduser(options.conf))
        if not os.path.isfile(conf):
            print "ERROR: Configutarion file " + conf + " not found."
            sys.exit(1)    
        
        teefaaobj = Teefaa(conf, True)
        status = teefaaobj.provision(options.host, options.os, options.site)
        if status != 'OK':
            print status
        else:
            print "Teefaa provisioned the host " + options.host + " of the site " + options.site + " with the os " + options.os + " successfully"
    elif (options.subparser_name == 'info'):
        status = teefaaobj.listImages(options.images)
        
if __name__ == "__main__":
    main()
