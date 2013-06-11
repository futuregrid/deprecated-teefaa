#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -------------------------------------------------------------------------- #
# Copyright 2012-2013, Indiana University                                    #
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
Description: Simplified Dynamic Provisioning. Creates an OS snapshot, installs snapshot on Bare Metal machines.
"""
__author__ = 'Koji Tanaka, Javier Diaz'

import time
import ConfigParser
import argparse
import re
import os
import logging
import logging.handlers
import sys
import string
import time
import paramiko
import random
import yaml
import sh
from subprocess import Popen, PIPE
from platform import dist

class TeefaaProcess():

    def __init__(self):
        
        self.defaultconfigfile = "teefaa.conf"
        self.opsys = dist()[0].lower() + dist()[1].replace('.', '')

    def set_conf(self):
        
        localpath = "~/.teefaa/"
        self.configfile = os.path.expanduser(localpath) \
                          + "/" + self.defaultconfigfile                          

        if not os.path.isfile(self.configfile):
            self.configfile = "/etc/futuregrid/" + self.defaultconfigfile

            if not os.path.isfile(self.configfile):
                print "ERROR: teefaa configuration file " + self.configfile + " not found"
                sys.exit(1)
    
        return self.configfile

    def shell(self, cmd, args='', fail_stop=True):

        sp = Popen(cmd.split() + args.split(), stdout=PIPE, stderr=PIPE)
        out, err = sp.communicate()
        rc = sp.returncode

        if fail_stop == True and rc != 0:

            print "Error in: {0} {1} \n\n{2}".format(cmd, args, err)
            sys.exit(1)
        else:
            return (out, err, rc)

    def shell_loop(self, cmd):

        for line in cmd:
            out, err, rc = self.shell(line)
            print out

    def awk(self, output, key, x, y=None):
        """ Test """

        res = []

        for line in output.split('\n'):
            line = ' '.join(line.split())
            expr = re.compile(key)
            if expr.search(line) != None:
               res.append(line.split()[x - 1])
        
        if y !=None:
            out = res[y - 1]

        else:
            out = '\n'.join(res)
        
        return out

    def check_commands(self, cmd_list):
        
        for cmd in cmd_list.split():

            out, err, rc = self.shell('which', cmd, fail_stop=False)
            if rc != 0:

                print "{0} is not installed.".format(cmd)
                sys.exit(1)

    def shell_fail_exit(self, cmd, args):

        out, err, rc = self.shell(cmd, args)
        if rc != 0:
            print "Error: while {0}\n {1}".format(cmd, err)
            sys.exit(1)

    def cmdrun(self, cmd):

        child = Popen(cmd.split(), stdout=PIPE)
        streamdata = child.communicate()[0]
        rc = child.returncode

        return (streamdata, rc)

    def ssh_try(self, host, username="root"):

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, username, timeout=5)
        except:
            print "Could not connect to {0}".format(host)

        ssh.close()

    def ssh_wait(self, host, user, key_path, limit=30):

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        count = 1
        while True:
            print "Trying to connect to {0} ({1}/{2})".format(host, count, limit)

            try:
                ssh.connect(host, username=user, key_filename=key_path, timeout=5)
                break
            except:
                print "Checking instances... Could not connect to {0}, waiting \
                        for it to start".format(host)
                count = count + 1
                time.sleep(5)

            if count == limit:
                print "Cound not connect to %s, giving up" % host
                sys.exit(1)
        
        print "SSH connection is fine now."
        ssh.close()

    def upload_image(self, host, user, key_path, snapshot):

        # Create directory to mount image.
        length = 10
        chars = string.ascii_letters + string.digits
        random.seed = (os.urandom(1024))
        random_name = ''.join(random.choice(chars) for i in range(length))
        # Send snapshot
        print "sending snapshot..."
        cmd = "scp -i {0} {1} {2}@{3}:{4}.squashfs".format(
                   key_path, snapshot, user, host, random_name)
        out, err, rc = self.shell(cmd)
        # Create a directory
        cmd = "ssh -i {0} {1}@{2} mkdir /mnt/{3}".format(
                   key_path, user, host, random_name)
        out, err, rc = self.shell(cmd)
        # Mount the image
        cmd = "ssh -i {0} {1}@{2} mount -o loop {3}.squashfs /mnt/{4}".format(
                   key_path, user, host, random_name, random_name)
        out, err, rc = self.shell(cmd)

        print '''Your image is ready. Set this on your image.list

           {0}:/mnt/{1}
        '''.format(host, random_name)

class Snapshot():
   
    def __init__(self, config_file):

        self.conf = ConfigParser.ConfigParser()
        self.conf.read(config_file)
        self.snapshot_dir = self.conf.get('snapshot', 'snapshot_dir').strip('"').strip('\'')
        self.user_exclude = self.conf.get('snapshot', 'exclude_dirs').strip('"').strip('\'')
        self.exclude_list = "proc/*,sys/*,dev/*,tmp/*,mnt/*,media/*," \
                            + self.snapshot_dir.strip('/') + '/*'

    def create_snapshot(self):

        p = TeefaaProcess()

        # Check required commands
        cmd_list = "mksquashfs rsync"
        p.check_commands(cmd_list)

        # Copy system image
        temp_dir = self.snapshot_dir + '/rootimg'
        hostname = p.shell("hostname -s")[0].strip()
        timestamp = p.shell("date +%Y-%m%d-%H%M")[0].strip()
        cmd = "mkdir -p {0}".format(temp_dir)
        out, err, rc = p.shell(cmd)
        if rc != 0:
            cmd = 'rsync -a --delete'
        else:
            cmd = 'rsync -a'

        exclude_list = self.exclude_list.split(',')
        var = 0
        while var < len(exclude_list):
            append = ' '.join(['--exclude', exclude_list[var]])
            cmd = ' '.join([cmd, append])
            var = var + 1
        cmd = ' '.join([cmd, '/', temp_dir])
        print "Coping system to %s..." % temp_dir
        p.cmdrun(cmd)

        # Make snapshot
        snapshot_file = "%s/%s-%s.squashfs" % (self.snapshot_dir, hostname, timestamp)
        print "Making snapshot..."
        cmd = "mksquashfs %s %s -noappend" % (temp_dir, snapshot_file)
        output, rc = p.cmdrun(cmd)
        print output
        cmd = "rm -rf %s" % temp_dir
        output, rc = p.cmdrun(cmd)
        print output

class Repository():

    def __init__(self, config_file, snapshot):

        self.conf = ConfigParser.ConfigParser()
        self.conf.read(config_file)
        self.key_name = self.conf.get('repository', 'key_name').strip('"').strip('\'')
        self.key_path = self.conf.get('repository', 'key_path').strip('"').strip('\'')
        self.key_path = os.path.expandvars(os.path.expanduser(self.key_path))
        self.image = self.conf.get('repository', 'repo_image').strip('"').strip('\'')
        self.snapshot = snapshot

    def create_repo(self):

        # Load TeefaaProcess as p
        p = TeefaaProcess()

        # Check if euca2ools works fine.
        output, rc = p.cmdrun("euca-describe-instances")
        if rc != 0:
            print "Error: euca-describe-instances failed \n %s" % output
            sys.exit(1)
        
        # Run repo instance
        print "Start instance..."
        cmd = "euca-run-instances -k %s %s" % (self.key_name, self.image)
        output, rc = p.cmdrun(cmd)
        awkout = p.awk(output, "INSTANCE", 2)
        instance = awkout

        # Check if it is running
        count = 1
        limit = 50

        while True:

            cmd = "euca-describe-instances %s" % instance
            output, rc = p.cmdrun(cmd)
            awkout = p.awk(output, "INSTANCE", 6)
            status = awkout

            if status == "running":
            
                print "Now instance is running"
                break

            elif status == "error":

                print "Error: status of instance is error"
                sys.exit(1)

            print "Checking instance... Status is %s, wait for it to be running (%i/%i)" \
                    % (status, count, limit)
            count = count + 1
            time.sleep(5)

            if count == limit:

               print "Status is still", status, ", giving it up."
               sys.exit(1)

        count = 1
        limit = 50

        while True:
            # Get IP address
            cmd = "euca-describe-instances %s" % instance
            output, rc = p.cmdrun(cmd)
            awkout = p.awk(output, "INSTANCE", 14)
            ip_address = awkout
            # Check if the instance responds to ping
            cmd = "ping -c 3 %s" % ip_address
            output, rc = p.cmdrun(cmd)
            if rc == 0:
                print "Now instance is reachable"
                break
            print "Checking instance... Waiting for %s(%s) to be able to ping (%i/%i)" \
                    % (instance, ip_address, count, limit)
            count = count + 1
            time.sleep(5)
            if count == limit:
                print "Error: Couldn't get the ping response from %s(%s), gave it up" \
                       % (instance, ip_address)
                sys.exit(1)

        p.ssh_wait(host=ip_address, user='root', key_path=self.key_path, limit=30)

        # Upload snapshot
        p.upload_image(host=ip_address, user='root', key_path=self.key_path, snapshot=self.snapshot)

class Bootstrap():

    def __init__(self, config_file):
        
        self.conf = ConfigParser.ConfigParser()
        self.conf.read(config_file)
        self.part = {}
        self.part['disk'] = self.conf.get('partitioning', 'disk').strip('"').strip('\'')
        self.part['sizes'] = self.conf.get('partitioning', 'sizes').replace('|', '').split()
        self.part['types'] = self.conf.get('partitioning', 'types').replace('|', '').split()
        self.part['mount'] = self.conf.get('partitioning', 'mount').replace('|', '').split()
        self.repo = self.conf.get('image', 'image_repo').replace(',', ' ').split()
        self.diffs = self.conf.get('image', 'diffs').strip('"').strip('\'')
        self.diff_name = 'custom1'
        self.diff_list = '~/Documents/workspace/teefaa/etc/diff.list'

    def partitioning(self):

        p = TeefaaProcess()
        parted = "parted /dev/{0} --script --".format(self.part['disk'])
        cmd = []
        cmd.append("{0} mklabel msdos".format(parted))
        cmd.append("{0} unit MB".format(parted))
        num = len(self.part['sizes'])
        sum = 1
        c = 0
        while c < num:
            size = int(self.part['sizes'][c])
            type = self.part['types'][c]
            if size > 0:
                size *= 1000

                if type == 'swap':
                    cmd.append("{0} mkpart primary linux-swap {1} {2}".format(
                                parted, sum, sum + size))

                else:
                    cmd.append("{0} mkpart primary {1} {2}".format(
                                parted, sum, sum + size))

            elif size == -1 and partition_type = 'mbr':
                cmd.append("{0} mkpart primary {1} 2000000".format(parted, sum))

            elif size == -1 and partition_type = 'gpt':
                cmd.append("{0} mkpart primary {1} -1".format(parted, sum))

            else:
                print "Error: partition size is not set properly"
                sys.exit(1)
            sum += size
            c += 1

        print '\n'.join(cmd)
        #p.shell_loop(cmd)

    def make_fsys(self):

        cmd = []
        disk = self.part['disk']
        num = len(self.part['sizes'])
        c =0
        while c < num:
            type = self.part['types'][c]
            mount = self.part['mount'][c]
            if type == 'swap':
                cmd.append("mkswap /dev/{0}{1}".format(disk, c + 1))
            elif type == 'ext3' or type == 'ext4' or type == 'xfs':
                cmd.append("mkfs.{0} /dev/{1}{2}".format(type, disk, c + 1))
                if mount == '/':
                    cmd.append("mount /dev/{0}{1} /mnt".format(disk, c + 1))
                elif mount != 'none':
                    cmd.append("mkdir -p /mnt/{0}".format(mount))
                    cmd.append("mount /dev/{0}{1} /mnt/{2}".format(disk, c + 1, mount))
            else:
                print "Error: {0} is not in the supported partition type".format(type)
                sys.exit(1)

            c += 1

        print '\n'.join(cmd)

    def copy_image(self):

        cmd = []
        repo = self.repo
        num = len(repo)
        img = random.randint(0, num - 1)

        exclude = "proc/*,sys/*,dev/*,tmp/*,mnt/*,media/*".split(',')
        x = "rsync -av "
        for a in exclude:
            x += "--exclude=\"{0}\" ".format(a)
        x += "{0}/ /mnt".format(repo[img])
        cmd.append(x)

        print '\n'.join(cmd)

    def check_os(self):

        opsys = dist()[0].lower() + dist()[1].replace('.', '')

        return opsys

    def update_diffs(self, custom=None):

        p = TeefaaProcess()
        cmd = []

        if custom == None:
            real_root = os.open("/", os.O_RDONLY)
            os.chroot('/mnt')
            diff_name = dist()[0].lower() + dist()[1].split('.')[0]
        else:
            diff_name = custom
        diffdir = self.diffs + '/' + self.diff_name

        rsync = 'rsync -av {0}/ /mnt'.format(diffdir)
        cmd.append(rsync)

        diff_list = p.shell('tree -if', diffdir)
        


class Provisioning():

    def __init__(self, repo, number, hours):

        self.repo = repo
        self.number = number
        self.hours = hours
        self.dir = os.path.expandvars(os.path.expanduser('~/.teefaa'))

        p = TeefaaProcess()

        if not os.path.isdir(self.dir):

            print "{0} has been created for storing config files".format(self.dir)
            p.shell('mkdir', self.dir)

        keydir = os.path.expandvars(os.path.expanduser('~/.ssh'))
        if os.path.isfile(keydir + '/id_rsa'):
            self.pubkey = keydir + '/id_rsa.pub'

        elif os.path.isfile(keydir + '/id_dsa'):
            self.pubkey = keydir + '/id_dsa.pub'

        else:
            print "Error: You don't have ssh key pair. Please create it."
            sys.exit(1)
            
    def create_exclude_list(self):

        exclude = '''
                  lost+found
                  proc/*
                  sys/*
                  dev/*
                  tmp/*
                  mnt/*
                  media/*
                  nexports/*
                  var/lib/teefaa/*
                  '''
        exclude = '\n'.join(exclude.split())
        f = open(self.dir + '/exclude.list', 'w+')
        f.write(exclude)
        f.write('\n')
        f.close()

    def create_image_list(self):

        image = "myimage {0}".format(self.repo)
        f = open(self.dir + '/image.list', 'w+')
        f.write(image)
        f.write('\n')
        f.close()

    def create_userrc(self):

        hours = str(self.hours)
        pubkey = open(self.pubkey).read().strip()

        userrc ='''IMAGE_NAME=myimage
                   SSH_PUBKEYS="{0}"
                   HOURS={1}
                   PARTITION_TYPE=mbr
                   disk=sda
                   sda1=(2 swap none)
                   sda2=(100 ext4 "/")
                   sda3=(-1 xfs "/data")'''.format(pubkey, hours)

        f = open(self.dir + '/userrc', 'w+')
        for line in userrc.split('\n'):
            f.write(line.strip() + '\n')
        f.close()
        
    def create_jobscript(self):

        number = str(self.number)

        jobscript = '''#!/bin/bash
                       #PBS -N PROVISIONING
                       #PBS -l nodes={0}:ppn=8
                       #PBS -q provision
                       module load torque
                       USERRC=~/.teefaa/userrc
                       IMAGE_LIST=~/.teefaa/image.list
                       EXCLUDE_LIST=~/.teefaa/exclude.list
                       sleep 10
                       source $USERRC
                       pbsdsh cp $USERRC /tmp/userrc
                       pbsdsh cp $IMAGE_LIST /tmp/image.list
                       pbsdsh cp $EXCLUDE_LIST /tmp/exclude.list
                       pbsdsh echo "Node $HOSTNAME will reboot with your image in 10~15 minutes."
                       sleep 10'''.format(number)

        f = open(self.dir + '/provisioning.pbs', 'w+')
        for line in jobscript.split('\n'):
            f.write(line.strip() + '\n')
        f.close()

    def boot(self):

        self.create_exclude_list()
        self.create_image_list()
        self.create_userrc()
        self.create_jobscript()

        p = TeefaaProcess()
        out, err, rc = p.shell('qsub {0}/provisioning.pbs'.format(self.dir))
        if rc == 0:
            print 'Provisioning is scheduled.'
        else:
            print 'Failed to schedule your provisioning.'
            sys.exit(1)

def main():

    parser = argparse.ArgumentParser(
            prog="teefaa", 
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="FutureGrid Teefaa Dynamic Provisioning")
    subparser = parser.add_subparsers(
            dest='subparser_name', 
            help='')
    create_snapshot = subparser.add_parser(
            'create-snapshot', 
            help='Create a snapshot of OS image')
    create_repo = subparser.add_parser(
            'create-repo', 
            help='Create a repository of OS image')
    create_repo.add_argument(
            '--snapshot', 
            dest="snapshot", 
            required=True, 
            metavar='/path/to/snapshot.squashfs', 
            help='Set the path to your snapshot file')
    bootstrap = subparser.add_parser(
            'bootstrap', 
            help='Install OS image')
    boot = subparser.add_parser(
            'boot', 
            help='Boot OS Image')
    boot.add_argument(
            '--repo',
            dest='repo',
            required=True,
            metavar='<IP Address|Hostname>:/path/to/image',
            help='Set your image repository')
    boot.add_argument(
            '--number',
            dest='number',
            required=True,
            metavar='Number',
            help='Set number of host to provision your image')
    boot.add_argument(
            '--hours',
            dest='hours',
            required=True,
            metavar='Hours',
            help='Set how many hours to reserve nodes')
    create_snapshot = subparser.add_parser(
            'test', 
            help='Test operations')

    options = parser.parse_args()

    teefaa = TeefaaProcess()
    config = teefaa.set_conf()

    if (options.subparser_name == 'create-snapshot'):
        snapshot = Snapshot(config)
        snapshot.create_snapshot()

    elif (options.subparser_name == 'create-repo'):
        repo = Repository(config, options.snapshot)
        repo.create_repo()

    elif (options.subparser_name == 'boot'):
        prov = Provisioning(repo=options.repo, 
                   number=options.number, 
                   hours=options.hours)
        prov.boot()

    elif (options.subparser_name == 'bootstrap'):

        btest= Bootstrap(config)
        btest.partitioning()
        #btest.make_fsys()
        #btest.copy_image()
        print 'test'
        

if __name__ == "__main__":
    main()
