#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# tfutils - installs utilities.
#

import os
import sys
from fabric.api import *
from fabric.contrib import *
from cuisine import *

@task
def install_pdsh():
    ''':opsys=XXXXX | Installs Parallel Distributed Shell'''
    if not env.user == 'root':
        print 'You need to login as root'
        exit(1)
    if dir_exists('/opt/pdsh-2.26'):
        print 'pdsh-2.26 is already installed.'
        exit(1)
    #package_update()
    distro = run('python -c "import platform; print platform.dist()[0].lower()"')
    if distro == 'centos' or \
            distro == 'redhat' or \
            distro == 'fedora':
        select_package('yum')
        package_update('audit')
        package_ensure('make gcc wget bzip2 openssl')
    elif distro == 'ubuntu' or \
            distro == 'debian':
        select_package('apt')
        package_update()
        package_ensure('build-essential')
    else:
        print '%s is not supported.' % distro
        print 'currently supported: centos, redhat, ubuntu, debian'
    dir_ensure('/root/source')
    with cd('/root/source'):
        run('wget http://pdsh.googlecode.com/files/pdsh-2.26.tar.bz2')
        run('tar jxvf pdsh-2.26.tar.bz2')
    with cd('/root/source/pdsh-2.26'):
        run('./configure --prefix=/opt/pdsh-2.26 \
                         --without-rsh --with-ssh \
                         --with-dshgroups=/opt/pdsh-2.26/dshgroups')
        run('make')
        run('make install')
    with cd('/root'):
        files.append('.bashrc', 'export PATH=/opt/pdsh-2.26/bin:$PATH')

@task
def install_parallel(prefix=/usr/local):
    ''':prefix=(default:/usr/local)'''
    with lcd('/tmp'):
        local('wget http://ftp.gnu.org/gnu/parallel/parallel-20130522.tar.bz2')
        local('tar jxvf http://ftp.gnu.org/gnu/parallel/parallel-20130522.tar.bz2')
    with lcd('/tmp/parallel-20130522'):
        local('./configure --prefix=%s' % prefix)
        local('make')
        local('make install')
