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

defaultconfigfile = "teefaa1.0.conf"

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
        self.generalconfig = None # general config parser

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
        Set the default confituration file when configuration file is not provided.
        '''
        
        localpath = "~/.fg/"
        self.configfile = os.path.expanduser(localpath) + "/" + defaultconfigfile
        if not os.path.isfile(self.configfile):
            self.configfile = "/etc/futuregrid/" + defaultconfigfile
            
            if not os.path.isfile(self.configfile):
                print "ERROR: teefaa configuration file " + self.configfile + " not found"
                sys.exit()
                
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
        
        section = 'Default'
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
            self.logDir = os.path.expanduser(config.get(section, 'log_dir', 0))
        except ConfigParser.NoOptionError:
            print "No log_dir option found in section " + section + " file " + self.configfile
            sys.exit(1)
            
        return config
    
    def errorMsg(self, msg):
        
        self.logger.error(msg)
        if self.verbose:
            print msg
    
    def loadSpecificConfig(self, host, image):
        '''This load the configuration of the site, machine and image to provision.
        Returns None or a dictionary.'''
        
        info = {}
        
        #Default configuraton
        section = 'Default'
        
        try:
            info['pxe_server'] = self.generalconfig.get(section, 'pxe_server', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No pxe_server option found in section " + section + " file " + self.configfile)
            return
        except ConfigParser.NoSectionError:
            self.errorMsg("Error: no section " + section + " found in the " + self.configfile + " config file")
            return
        try:
            info['git_remote_prefix'] = self.generalconfig.get(section, 'git_remote_prefix', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No git_remote_prefix option found in section " + section + " file " + self.configfile)
            return
        try:
            info['image_dir'] = self.generalconfig.get(section, 'image_dir', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No image_dir option found in section " + section + " file " + self.configfile)
            return
        try:
            info['pxe_conf_dir'] = self.generalconfig.get(section, 'pxe_conf_dir', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No pxe_conf_dir option found in section " + section + " file " + self.configfile)
            return
        try:
            info['netboot_conf'] = self.generalconfig.get(section, 'netboot_conf', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No netboot_conf option found in section " + section + " file " + self.configfile)
            return
        try:
            info['localboot_conf'] = self.generalconfig.get(section, 'localboot_conf', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No localboot_conf option found in section " + section + " file " + self.configfile)
            return
        try:
            info['part_batch_dir'] = self.generalconfig.get(section, 'part_batch_dir', 0)
        except ConfigParser.NoOptionError:
            self.errorMsg("No part_batch_dir option found in section " + section + " file " + self.configfile)
            return
        
        return info
    
    def executeCMD(self, CMD, errormsg):
        
        try:
            self.logger.debug(CMD)
            
            if self.verbose:
                subprocess.check_call(CMD, shell=True)
            else:
                p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                std = p.communicate()
                if p.returncode != 0:
                    msg = errormsg + " cmd= " + CMD + ". stderr= " + std[1]
                    self.logger.error(msg)
                    return msg
        except subprocess.CalledProcessError:
            msg = errormsg + " cmd= " + CMD
            self.logger.error(msg)
            return msg
    
    def provision(self, host, image):
        
        info = self.loadSpecificConfig(host, image)
        
        #Test Begin
        #print " Provisioning " + host + " with the image \"" + image + "\""
        #print str(info)
        #return 'OK'
        #Test End
        
        if info != None:
            try:
                # Get ready to netboot
                CMD = "echo ssh -oBatchMode=yes " + info['pxe_server'] + " cp " + info['pxe_conf_dir'] + "/" + info['netboot_conf'] + " " + info['pxe_conf_dir'] + "/" + host
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
            
            #
            # REBOOT HOST 
            #
            try:
                CMD = "echo ssh -oBatchMode=yes " + info['pxe_server'] + " rpower " + host + " boot"
                self.logger.debug(CMD)
                #
                #TODO: rpower command will be replaced to ipmi command soon.
                #
                
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
            
            #TODO: Prevent to wait forver.
            self.logger.debug(host + " is booting and not ready yet...")
            CMD = "echo ssh -q -oBatchMode=yes -o \"ConnectTimeout 5\" " + host + " " + "hostname > /dev/null 2>&1"
            self.logger.debug(CMD)
            p = 1
            while (not p == 0):
                p = subprocess.call(CMD, shell=True)
                if self.verbose:
                    print ""
                    print host + " is booting and not ready yet..."
                    print ""
                time.sleep(5)
            self.logger.debug(host + " has started with the auxiliary netboot image.")
            
            #
            # SWITCH IT BACK TO LOCAL BOOT
            #
            try:
                CMD = "echo ssh -oBatchMode=yes " + info['pxe_server'] + " cp /tftpboot/pxelinux.cfg/localboot /tftpboot/pxelinux.cfg/" + host
                
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
            
            #
            # PARTITIONING
            #
            #TODO: Add argumetn of partitioning dir
            try:
                CMD = "echo ssh " + host + " fdisk /dev/sda < " + info['part_batch_dir'] + "/" + image + ".batch"
                
                self.logger.debug(CMD)
                
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Partitioning failed. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Partitioning failed. cmd= " + CMD
                self.logger.error(msg)
                return msg
            # mkswap /dev/sda1
            try:
                CMD = "echo ssh " + host + " mkswap /dev/sda1"
                
                self.logger.debug(CMD)
                
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Failed to make swap. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Failed to make swap. cmd= " + CMD
                self.logger.error(msg)
                return msg
            # swapon /dev/sda1
            try:
                CMD = "echo ssh " + host + " swapon /dev/sda1"
                
                self.logger.debug(CMD)
                
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Failed to turn swap on. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Failed to turn swap on. cmd= " + CMD
                self.logger.error(msg)
                return msg
            # mkfs.ext4(or mkfs.ext3) /dev/sda2
            try:
                CMD = "echo ssh " + host + " mkfs.ext4 /dev/sda2"
                
                self.logger.debug(CMD)
                
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Failed to make filesystem. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Failed to make filesystem. cmd= " + CMD
                self.logger.error(msg)
                return msg
            
            # mount /dev/sda2 /mnt
            try:
                CMD = "echo ssh " + host + " mount /dev/sda2 /mnt"
                
                self.logger.debug(CMD)
                
                if self.verbose:
                    subprocess.check_call(CMD, shell=True)
                else:
                    p = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    std = p.communicate()
                    if p.returncode != 0:
                        msg = "ERROR: Failed to mount /dev/sda2. cmd= " + CMD + ". stderr= " + std[1]
                        self.logger.error(msg)
                        return msg
            except subprocess.CalledProcessError:
                msg = "ERROR: Failed to mount /dev/sda2. cmd= " + CMD
                self.logger.error(msg)
                return msg
            
            #
            # COPY IMAGE TO HOST:/MNT
            #
            # rsync -av image_dir/image/ host:/mnt
            CMD = "echo rsync -av --exclude=\".git\" " + info['image_dir'] + "/" + image + "/ " + host + ":/mnt"
            self.executeCMD(CMD, "ERROR: Failed to copy image")
            
            #
            # DOWNLOAD INDIVIDUAL CONFIG VIA GIT REPOSITORY
            #
            CMD = "echo ssh " + host + " git clone -b " + host + " " + info['git_remote_prefix'] + image + ".git"
            self.executeCMD(CMD, "ERROR: Failed to git clone.")
            
            #
            # COPY THEM TO /MNT
            #
            CMD = "echo ssh " + host + " rsync -av --exclude=\".git\" " + image + "/ " + host + ":/mnt"
            self.executeCMD(CMD, "ERROR: Failed to coping indivicual files.")
            
            #
            # INSTALL GRUB
            #
            CMD = "echo GRUB TEST"
            self.executeCMD(CMD, "ERROR: This is test.")
            
            return 'OK'
            
        else:
            msg = "ERROR: Reading configuration for host " + host + ", image " + image
            self.logger.error(msg)
            return msg

def main():
    parser = argparse.ArgumentParser(prog="teefaa", formatter_class=argparse.RawDescriptionHelpFormatter,
            description="FutureGrid Teefaa Dynamic Provisioning Help ")
    parser.add_argument('--host', dest="host", required=True, metavar='hostname', 
            help='Host that will be provisioned with a new OS.')
    parser.add_argument('--conf', dest="conf", metavar='config_file', default="/opt/teefaa/etc/teefaa1.0.conf", 
            help='Configuration file.')
    parser.add_argument('--image', dest="image", required=True, metavar='image', 
            help='Name of the OS image that will be provisioned.')
    parser.add_argument('--verbose', dest="verbose", metavar='verbose', default=False,
            help='Verbose mode True or False, default=False')
    
    options = parser.parse_args()
    
    conf = os.path.expandvars(os.path.expanduser(options.conf))
    
    if not os.path.isfile(conf):
        print "ERROR: Configutarion file " + conf + " not found."
        sys.exit(1)
    
    teefaaobj = Teefaa(conf, options.verbose)
    status = teefaaobj.provision(options.host, options.image)
    if status != 'OK':
        print status
    else:
        print " Teefaa provisioned the host " + options.host + " of the image " + options.image + " successfully"

if __name__ == "__main__":
    main()
