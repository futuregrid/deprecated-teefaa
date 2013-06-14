#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import sys
from fabric.api import *
from fabric.contrib import *
from cuisine import *

def backup(item):
    '''| Backup System'''
    cfgfile = 'ymlfile/system/backup.yml'
    f = open(cfgfile)
    cfg = yaml.safe_load(f)[item]
    f.close()
