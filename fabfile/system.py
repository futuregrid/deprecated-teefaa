#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import sys
import yaml
import datetime
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

    _backup_rsync(cfg)
    _backup_squashfs(cfg, item)

def _backup_rsync(cfg):
    '''Execute rsync'''
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

def _backup_squashfs(cfg, item):
    '''Make squashfs'''
    if cfg['mksquashfs']:
        today = datetime.date.today
        save_as = '%s/%s-%s.squashfis' % (cfg['dir_squashfs'],item,today)
        cmd = []
        cmd.append('echo mksquashfs')
        cmd.append(cfg['dest'])
        cmd.append(save_as)
        cmd.append('-noappend')

        cmd = ' '.join(cmd)
        local(cmd)
