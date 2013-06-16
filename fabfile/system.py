#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# system.py - is a set of tools for system management.
#

import os
import sys
import yaml
import datetime
from fabric.api import *
from fabric.contrib import *
from cuisine import *

def _read_ymlfile(ymlfile):
    '''Read YAML file'''
    if not os.path.exists(ymlfile):
        print '%s doesn\'t exist.' % ymlfile
        exit(1)
    f = open(ymlfile)
    yml = yaml.safe_load(f)
    f.close()

    return yml

@task
def users_ensure(group):
    ''':group=XXXXX | Ensure Users exists'''
    ymlfile = 'ymlfile/system/users.yml'
    users = _read_ymlfile(ymlfile)[group]
    for user in users:
        name = user
        options = users[user]
        passwd,home,uid,gid,shell,fullname =None,None,None,None,None,None
        if options['passwd']:
            passwd = options['passwd']
        if options['home']:
            home = options['home']
        if options['uid']:
            uid = options['uid']
        if options['gid']:
            gid = options['gid']
        if options['shell']:
            shell = options['shell']
        if options['fullname']:
            fullname = options['fullname']
        user_ensure(name, passwd, home, uid, gid, shell, fullname, encrypted_passwd=True)
        user_home = user_check(user, need_passwd=False)['home']
        dot_ssh = '%s/.ssh' % user_home
        with mode_sudo():
            dir_ensure(dot_ssh, mode=700, owner=user)
        for key in options['authorized_keys']:
            with mode_sudo():
                ssh_authorize(user, key)

@task
def backup(item):
    ''':item=XXXXX | Backup System'''
    if not os.getenv('USER') == 'root':
        print 'You have to be root.'
        exit(1)

    cfgfile = 'ymlfile/system/backup.yml'
    if not os.path.exists(cfgfile):
        print '%s doesn\'t exist.' % cfgfile
        exit(1)
    f = open(cfgfile)
    cfg = yaml.safe_load(f)[item]
    f.close()

    _backup_rsync(cfg)
    _backup_squashfs(cfg, item)

@task
def backup_list():
    ''':item=XXXXX | Show the list of backup'''
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
        save_as = '%s/%s-%s.squashfs' \
                % (cfg['dir_squashfs'],item,today())
        cmd = []
        cmd.append('mksquashfs')
        cmd.append(cfg['dest'])
        cmd.append(save_as)
        cmd.append('-noappend')

        cmd = ' '.join(cmd)
        local(cmd)

