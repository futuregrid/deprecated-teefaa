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

@task
def backup_list():
    ''':item=XXXXX | Backup System'''
    cfgfile = 'ymlfile/system/backup.yml'
    f = open(cfgfile)
    cfg = yaml.safe_load(f)
    f.close()

    n = 1
    for item in cfg:
        if n == 1:
            print ''
        print " %s. %s" % (n, item)
        n += 1

def _backup_rsync(cfg):
    '''Execute rsync'''
    cmd = []
    cmd.append('rsync -av')

    if not os.path.isdir(cfg['dest']):
        local('mkdir -p %s' % cfg['dest'])

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
        save_as = '%s/%s-%s.squashfs' % (cfg['dir_squashfs'],item,today())
        cmd = []
        cmd.append('mksquashfs')
        cmd.append(cfg['dest'])
        cmd.append(save_as)
        cmd.append('-noappend')

        cmd = ' '.join(cmd)
        local(cmd)
