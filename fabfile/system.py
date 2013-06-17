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
from teefaa import read_ymlfile, check_distro


@task
def users_force_resetpass(group):
    ''':group=XXXXX | Force users to reset password'''

    ymlfile = 'ymlfile/system/users.yml'
    users = read_ymlfile(ymlfile)[group]

    for user in users:
        with mode_sudo():
            run('usermod -p \'\' %s' % user)
            run('chage -d 0 %s' % user)

@task
def users_ensure(group):
    ''':group=XXXXX | Ensure Users exists'''

    ymlfile = 'ymlfile/system/users.yml'
    users = read_ymlfile(ymlfile)[group]

    distro = check_distro()
    if distro == 'fedora':
        select_package('yum')
        package_ensure('openssl')

    for user in users:
        options = users[user]
        passwd,home,uid,gid,shell,fullname = None,None,None,None,None,None
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
        user_ensure(user, passwd, home, uid, gid, shell, fullname)
        user_home = user_check(user)['home']
        dot_ssh = '%s/.ssh' % user_home
        authorized_keys = '%s/authorized_keys' % dot_ssh
        with mode_sudo():
            dir_ensure(dot_ssh, mode=700, owner=user)
            if not file_exists(authorized_keys):
                run('touch %s' % authorized_keys)
                file_ensure(authorized_keys, mode=600, owner=user)
        for key in options['authorized_keys']:
            with mode_sudo():
                ssh_authorize(user, key)

@task
def backup(item):
    ''':item=XXXXX | Backup System'''
    if not os.getenv('USER') == 'root':
        print 'You have to be root.'
        exit(1)

    ymlfile = 'ymlfile/system/backup.yml'
    cfg = read_ymlfile(ymlfile)[item]

    _backup_rsync(cfg)
    _backup_squashfs(cfg, item)

@task
def backup_list():
    ''':item=XXXXX | Show the list of backup'''
    ymlfile = 'ymlfile/system/backup.yml'
    cfg = read_ymlfile(ymlfile)

    print 'Backup List:'
    n = 1
    for item in cfg:
        if n == 1:
            print ''
        print "    %s.  %s" % (n, item)
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

@task
def pxeboot(boottype, hostname):
    ''':boottype=XXXXX,hostname=XXXXX|PXE Boot'''
    cfgfile = 'ymlfile/system/pxecfg.yml'
    pxecfg = read_ymlfile(cfgfile)
    bootcfg = '%s/%s' % (pxecfg['pxeprefix'], boottype)
    hostcfg = '%s/%s' % (pxecfg['pxeprefix'], hostname)

    run('cat %s > %s' % (bootcfg, hostcfg))

@task
def pxeboot_list():
    ''':boottype=XXXXX,hostname=XXXXX|PXE Boot'''
    cfgfile = 'ymlfile/system/pxecfg.yml'
    pxecfg = read_ymlfile(cfgfile)

    output = run('ls %s' % pxecfg['pxeprefix'])
    print output

@task
def ipmi_power(hostname, action):
    ''':hostname=XXXXX,action=XXXXX'''
    cfgfile = 'ymlfile/system/ipmitool.yml'
    ipmicfg = read_ymlfile(cfgfile)[hostname]
    user = ipmicfg['user']
    password = ipmicfg['password']
    bmcaddr = ipmicfg['bmcaddr']

    output = run('ipmitool -I lanplus -U %s -P %s -E -H %s power %s' 
                     % (user, password, bmcaddr, action))
    print output
