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
        
        section = 'Main'
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
            return
        except ConfigParser.NoOptionError:
            self.errorMsg("No git_remote_prefix option found in section " + section + " file " + self.configfile)
            return
        try:
            info['image_dir'] = self.generalconfig.get(section, 'image_dir', 0)
            return
        except ConfigParser.NoOptionError:
            self.errorMsg("No image_dir option found in section " + section + " file " + self.configfile)
            return
    
    def provision(self, image):
        
        info = self.loadSpecificConfig(host, image)
        
        #Test Begin
        print " Provisioning " + host + " with the image \"" + image + "\""
        print str(info)
        return 'OK'
        #Test End

    
def main():
    parser = argparse.ArgumentParser(prog="teefaa", formatter_class=argparse.RawDescriptionHelpFormatter,
            description="FutureGrid Teefaa Dynamic Provisioning Help ")
    parser.add_argument('--host', dest="host", required=True, metavar='hostname', 
            help='Host that will be provisioned with a new OS.')
    parser.add_argument('--conf', dest="conf", metavar='config_file', default="/opt/teefaa/etc/teefaa1.0.conf", 
            help='Configuration file.')
    parser.add_argument('--image', dest="image", required=True, metavar='image', 
            help='Name of the OS image that will be provisioned.')
    
    options = parser.parse_args()
    
    conf = os.path.expandvars(os.path.expanduser(options.conf))
    
    if not os.path.isfile(conf):
        print "ERROR: Configutarion file " + conf + " not found."
        sys.exit(1)

    teefaaobj = Teefaa(conf, True)
    status = teefaaobj.provision(options.host, options.image)
    if status != 'OK':
        print status
    else:
        print "Teefaa provisioned the host " + options.host + " of the image " + options.image + " successfully"

if __name__ == "__main__":
    main()
