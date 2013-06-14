#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import sys
import yaml
from fabric.api import *
from fabric.contrib import *
from cuisine import *

@task
def backup(item):
    ''':item=XXXXX | Backup System'''
    cfgfile = 'ymlfile/system/backup.yml'
    f = open(cfgfile)
    cfg = yaml.safe_load(f)[item]
    f.close()

    cmd = []
    cmd.append('echo rsync -av')

    if cfg['one-file-system']:
        cmd.append('--one-file-system')

    if cfg['delete']:
        cmd.append('--delete')

    if cfg['exclude']:
        for a in cfg['exclude-list']:
            cmd.append('--exclude=\'%s\'' % a)

    cmd.append(cfg['src'])
    cmd.append(cfg['dest'])

    cmd = ' '.join(cmd)
    local(cmd)
