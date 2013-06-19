#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# scratch.py - is a collection of scripts for bootstrapping baremetal/virtual machines.
# 

import os
import sys
import yaml
import time
import datetime
from platform import dist
from fabric.api import *
from fabric.contrib import *
from cuisine import *

@task
def bootstrap(imagename):
    ''':imagename=XXXXX | Bootstrap OS'''

    if not env.user == 'root':
        print 'You need to login as root for bootstrap.'
        print 'So add the option \"--user root\"'
        exit(1)

    hostsfile = 'ymlfile/scratch/hosts.yml'
    hosts = read_ymlfile(hostsfile)

    imagesfile = 'ymlfile/scratch/images.yml'
    images = read_ymlfile(imagesfile)

    image = images[imagename]
    host = hosts[env.host]

    bootloader = image['bootloader']
    device = host['disk']['device']
    swap = host['disk']['partitions']['swap']
    system = host['disk']['partitions']['system']
    data = host['disk']['partitions']['data']
    scheme = image['partition_scheme']
    bootloader = image['bootloader']

    partitioning(device, swap, system, data, scheme)
    makefs(device, swap, system, data, scheme)
    mountfs(device, data, scheme)
    copyimg(image)
    condition(host, image, device, scheme)
    install_bootloader(device, image)

def partitioning(device, swap, system, data, scheme):
    '''mbr scheme partitioning'''

    run('aptitude update')
    package_ensure('parted')
    if scheme == 'mbr':
        run('parted %s --script -- mklabel msdos' % device)
        run('parted %s --script -- unit MB' % device)
        a, b = 1, int(swap['size']) * 1000
        run('parted %s --script -- mkpart primary linux-swap %s %s' % (device, a, b))
        bootid = 2
    elif scheme == 'gpt':
        run('parted %s --script -- mklabel gpt' % device)
        run('parted %s --script -- unit MB' % device)
        run('parted %s --script -- mkpart non-fs 1 3' % device)
        a, b = 3, int(swap['size']) * 1000
        run('parted %s --script -- mkpart swap linux-swap %s %s' % (device, a, b))
        run('parted %s --script -- set 1 bios_grub on' % device)
        bootid = 3
    else: 
        print 'ERROR: scheme %s is not supported.' % scheme
        exit(1)
    a, b = b, b + int(system['size']) * 1000
    run('parted %s --script -- mkpart primary %s %s' % (device, a, b))
    if data['size'] == '-1':
        a, b = b, -1
    else:
        a, b = b, b + int(data['size']) * 1000
    run('parted %s --script -- mkpart primary %s %s' % (device, a, b))
    run('parted %s --script -- set %s boot on' % (device, bootid))
    run ('parted %s --script -- print' % device)

def makefs(device, swap, system, data, scheme):
    '''Make Filesytem'''

    # Initialize partition number as;
    pnum = 1
    if scheme == 'gpt':
        pnum += 1
    package_ensure('xfsprogs')
    run('mkswap %s%s' % (device, pnum))
    pnum += 1
    run('mkfs.%s %s%s' % (system['type'], device, pnum))
    pnum += 1
    run('mkfs.%s -f %s%s' % (data['type'], device, pnum))

def mountfs(device, data, scheme):
    '''Mount Filesystem'''
    # Initialize partition number as;
    pnum = 1
    if scheme == 'gpt':
        pnum += 1
    run('swapon %s%s' % (device, pnum))
    pnum += 1
    run('mount %s%s /mnt' % (device, pnum))
    if not files.exists('/mnt%s' % data['mount']):
        run('mkdir -p /mnt%s' % data['mount'])
    pnum += 1
    run('mount %s%s /mnt%s' % (device, pnum, data['mount']))

def copyimg(image):
    '''Copy image'''
    remote = image['osimage']
    local = "/mnt/osimage.%s" % image['extension']
    method = image['method']
    mount = "/root/osimage"

    if method == "put":
        put(remote, local)
    elif method == "scp":
        run("scp %s %s" % (remote, local))
    elif method == "wget":
        run("wget %s -O %s" % (remote, local))
    elif method == "rsync":
        run("rsync -a --stats --one-file-system %s/ /mnt" % remote)
        run("rsync -a --stats --one-file-system %s/boot/ /mnt/boot" % remote)
    elif method == "btsync":
        run("mkdir -p /mnt/BTsync")
        run("ln -s /mnt/BTsync /BTsync")
        mkbtseed(image['btcfg'], image['btbin'])
        count = 0
        while not files.exists(image['osimage']):
            time.sleep(30)
            print "Waiting for the image to be ready... %s/20" % count
            count += 1
            if count > 41:
                print "ERROR: give up waiting btsync ready."
                exit(1)
        local = image['osimage']
    else:
        print "Error: method %s is not supported" % method
        exit(1)

    if not method == "rsync":
        if not files.exists(mount):
            run('mkdir -p %s' % mount)
        if image['extension'] == "tar.gz":
            run('tar zxvf %s -C /mnt' % local)
        elif image['extension'] == "squashfs" or \
                image['extension'] == "img" or \
                image['extension'] == "qcow2":
            run('mount %s %s -o loop' % (local, mount))
            run('rsync -a --stats %s/ /mnt' % mount)
            run('umount %s' % mount)
        else:
            print "Extension %s is not supported." % image['extension']
            exit(1)
        run('rm -f %s' % local)

def condition(host, image, device, scheme):
    '''Condition setting files'''
    if image['os'] == 'centos6' or \
            image['os'] == 'redhat6':
        condition_redhat6(host, image, device, scheme)
    elif image['os'] == 'ubuntu12' or \
            image['os'] == 'ubuntu13':
        condition_ubuntu12(host, image, device, scheme)

def condition_redhat6(host, image, device, scheme):
    '''Condition config files for Redhat6'''
    # Update fstab, mtab, selinux and udev/rules
    put('share/scratch/etc/fstab.%s' % image['os'], '/mnt/etc/fstab')
    put('share/scratch/etc/mtab.%s' % image['os'], '/mnt/etc/mtab')
    put('share/scratch/boot/grub/grub.conf.%s' % image['os'], '/mnt/boot/grub/grub.conf')
    data = host['disk']['partitions']['data']
    if data['mount']:
        if data['type'] == 'xfs':
            files.append('/mnt/etc/fstab', \
                    'DEVICE3 %s xfs defaults,noatime 0 0' % data['mount'])
        elif data['type'] == 'ext4' or \
                data['type'] == 'ext3':
            files.append('/mnt/etc/fstab', \
                    'DEVICE3 %s %s defaults 0 0' % (data['mount'], data['type']))
        else:
            print "ERROR: system type %s is not supported." % data['type']
            exit(1)
    if scheme == 'gpt':
        for a in 4,3,2:
            b = a - 1
            files.sed('/mnt/etc/fstab', 'DEVICE%s' % b, 'DEVICE%s' % a)
            files.sed('/mnt/etc/mtab', 'DEVICE%s' % b, 'DEVICE%s' % a)
            files.sed('/mnt/boot/grub/grub.conf', 'DEVICE%s' % b, 'DEVICE%s' % a)
    files.sed('/mnt/etc/fstab', 'DEVICE', device)
    files.sed('/mnt/etc/mtab', 'DEVICE', device)
    put('share/scratch/etc/selinux/config', '/mnt/etc/selinux/config')
    run('rm -f /mnt/etc/udev/rules.d/70-persistent-net.rules')
    run('rm -f /mnt/etc/sysconfig/network-scripts/ifcfg-eth*')
    run('rm -f /mnt/etc/sysconfig/network-scripts/ifcfg-ib*')
    # Disable ssh password login
    files.sed('/mnt/etc/ssh/sshd_config', 'PasswordAuthentication yes', 'PasswordAuthentication no')
    files.uncomment('/mnt/etc/ssh/sshd_config', 'PasswordAuthentication no')
    # Update Grub Configuration
    files.sed('/mnt/boot/grub/grub.conf', 'KERNEL', image['kernel'])
    files.sed('/mnt/boot/grub/grub.conf', 'RAMDISK', image['ramdisk'])
    files.sed('/mnt/boot/grub/grub.conf', 'OSNAME', image['os'])
    files.sed('/mnt/boot/grub/grub.conf', 'DEVICE', device)
    # Update Hostname
    file = '/mnt/etc/sysconfig/network'
    run('rm -f %s' % file)
    files.append(file, 'HOSTNAME=%s' % host['hostname'])
    files.append(file, 'NETWORKING=yes')
    # Update Network Interfaces
    for iface in host['network']:
        iface_conf = host['network'][iface]
        file = '/mnt/etc/sysconfig/network-scripts/ifcfg-%s' % iface
        #run('rm -f %s' % file)
        files.append(file, 'DEVICE=%s' % iface)
        files.append(file, 'BOOTPROTO=%s' % iface_conf['bootproto'])
        files.append(file, 'ONBOOT=%s' % iface_conf['onboot'])
        if iface_conf['bootproto'] == 'dhcp':
            pass
        elif iface_conf['bootproto'] == 'static' or \
                iface_conf['bootproto'] == 'none':
            files.append(file, 'IPADDR=%s' % iface_conf['ipaddr'])
            files.append(file, 'NETMASK=%s' % iface_conf['netmask'])
            if iface_conf['gateway']:
                files.append(file, 'GATEWAY=%s' % iface_conf['gateway'])
        else:
            print "ERROR: bootproto = %s is not supported."
            exit(1)
    # Delete key pair
    #if host['del_keypair']:

    # Update Authorized Keys
    if host['update_keys']:
        if not files.exists('/mnt/root/.ssh'):
            run('mkdir -p /mnt/root/.ssh')
            run('chmod 700 /mnt/root/.ssh')
        file = '/mnt/root/.ssh/authorized_keys'
        run('rm -f %s' % file)
        for key in host['pubkeys']:
            files.append(file, '%s' % host['pubkeys'][key])
        run('chmod 640 %s' % file)

def condition_ubuntu12(host, image, device, scheme):
    '''Condition config files for Redhat6'''
    # Update fstab, mtab, selinux and udev/rules
    put('share/scratch/etc/fstab.%s' % image['os'], '/mnt/etc/fstab')
    put('share/scratch/etc/mtab.%s' % image['os'], '/mnt/etc/mtab')
    data = host['disk']['partitions']['data']
    if data['mount']:
        if data['type'] == 'xfs':
            files.append('/mnt/etc/fstab', \
                    'DEVICE3 %s xfs defaults,noatime 0 0' % data['mount'])
        elif data['type'] == 'ext4' or \
                data['type'] == 'ext3':
            files.append('/mnt/etc/fstab', \
                    'DEVICE3 %s %s defaults 0 0' % (data['mount'], data['type']))
        else:
            print "ERROR: system type %s is not supported." % data['type']
            exit(1)
    if scheme == 'gpt':
        for a in 4,3,2:
            b = a - 1
            files.sed('/mnt/etc/fstab', 'DEVICE%s' % b, 'DEVICE%s' % a)
            files.sed('/mnt/etc/mtab', 'DEVICE%s' % b, 'DEVICE%s' % a)
    files.sed('/mnt/etc/fstab', 'DEVICE', device)
    files.sed('/mnt/etc/mtab', 'DEVICE', device)
    run('rm -f /mnt/etc/udev/rules.d/70-persistent-net.rules')
    # Disable ssh password login
    files.sed('/mnt/etc/ssh/sshd_config', 'PasswordAuthentication yes', 'PasswordAuthentication no')
    files.uncomment('/mnt/etc/ssh/sshd_config', 'PasswordAuthentication no')
    # Disable cloud-init
    for file in [
            '/mnt/etc/init/cloud-config.conf',
            '/mnt/etc/init/cloud-final.conf',
            '/mnt/etc/init/cloud-init.conf',
            '/mnt/etc/init/cloud-init-container.conf',
            '/mnt/etc/init/cloud-init-local.conf',
            '/mnt/etc/init/cloud-init-nonet.conf',
            '/mnt/etc/init/cloud-log-shutdown.conf'
            ]:
        if file_is_file(file):
            run('mv %s %s.bak' % (file, file))
    # Update hostname
    file = '/mnt/etc/hostname'
    run('rm -f %s' % file)
    files.append(file, '%s' % host['hostname'])
    # Update network interface
    file = '/mnt/etc/network/interfaces'
    run('rm -f %s' % file)
    files.append(file, 'auto lo')
    files.append(file, 'iface lo inet loopback')
    for iface in host['network']:
        iface_conf = host['network'][iface]
        files.append(file, '# Interface %s' % iface)
        files.append(file, 'auto %s' % iface)
        files.append(file, 'iface %s inet %s' % (iface, iface_conf['bootproto']))
        if iface_conf['bootproto'] == 'dhcp':
            pass
        elif iface_conf['bootproto'] == 'static':
            files.append(file, 'address %s' % iface_conf['ipaddr'])
            files.append(file, 'netmask %s' % iface_conf['netmask'])
            if iface_conf['gateway']:
                files.append(file, 'gateway %s' % iface_conf['gateway'])
            if iface_conf['nameserver']:
                files.append(file, 'dns-nameservers %s' % iface_conf['nameserver'])
    # Generate ssh host key if it doesn't exist.
    run('rm -f /mnt/etc/ssh/ssh_host_*')    
    run('ssh-keygen -t rsa -N "" -f /mnt/etc/ssh/ssh_host_rsa_key')
    # Update authorized_keys.
    if host['update_keys']:
        if not files.exists('/mnt/root/.ssh'):
            run('mkdir -p /mnt/root/.ssh')
            run('chmod 700 /mnt/root/.ssh')
        file = '/mnt/root/.ssh/authorized_keys'
        run('rm -f %s' % file)
        for key in host['pubkeys']:
            files.append(file, '%s' % host['pubkeys'][key])
        run('chmod 640 %s' % file)

def install_bootloader(device, image):
    '''Install Grub'''
    run('mount -t proc proc /mnt/proc')
    run('mount -t sysfs sys /mnt/sys')
    run('mount -o bind /dev /mnt/dev')
    if image['os'] == 'ubuntu12' or \
            image['os'] == 'ubuntu13':
            run('chroot /mnt update-grub')
    if image['rootpass'] == "reset":
        run('chroot /mnt usermod -p \'\' root')
        run('chroot /mnt chage -d 0 root')
    elif image['rootpass'] == "delete":
        run('chroot /mnt passwd --delete root')
    run('chroot /mnt grub-install %s --recheck' % device)
    run('sync')
    run('reboot')

@task
def mkbtseed(btcfg, btbin):
    ''':btcfg=XXXXX,btbin=XXXXX | Make a seed of Bittorrent Sync'''
    if not files.exists('/BTsync/image'):
        run('mkdir -p /BTsync/image')
    put(btcfg, '/BTsync/btsync.conf')
    put(btbin, '/BTsync/btsync', mode=755)
    files.sed('/BTsync/btsync.conf', 'DEVNAME', env.host)
    run('/BTsync/btsync --config /BTsync/btsync.conf')

@task
def make_livecd(livecd_name, livecd_cfg='ymlfile/scratch/livecd.yml'):
    ''':livecd_name=XXXXX,livecd_cfg=cfg/livecd.yaml | Make LiveCD'''
    f = open(livecd_cfg)
    livecd = yaml.safe_load(f)[livecd_name]
    f.close()

    packages = [
            'wget',
            'genisoimage',
            'squashfs-tools'
            ]
    for package in packages:
        package_ensure(package)
    run('wget %s -O /tmp/livecd.iso' % livecd['isoimage'])
    if not file_is_dir('/mnt/tfmnt'):
        run('mkdir /mnt/tfmnt')
    run('mount /tmp/livecd.iso /mnt/tfmnt -o loop')
    run('rsync -a --stats /mnt/tfmnt/ /tmp/imgdir')
    run('umount /mnt/tfmnt')
    run('mount -o loop /tmp/imgdir/live/filesystem.squashfs /mnt/tfmnt')
    run('rsync -a --stats /mnt/tfmnt/ /tmp/rootimg')
    run('umount /mnt/tfmnt')
    run('cat /etc/resolv.conf > /tmp/rootimg/etc/resolv.conf')
    run('mount -t proc proc /tmp/rootimg/proc')
    run('mount -t sysfs sys /tmp/rootimg/sys')
    run('mount -o bind /dev /tmp/rootimg/dev')
    run('chroot /tmp/rootimg aptitude update')
    run('chroot /tmp/rootimg aptitude -y install openssh-server vim squashfs-tools tree xfsprogs parted')
    run('chroot /tmp/rootimg ssh-keygen -N "" -C "root@teefaa" -f /root/.ssh/id_rsa')
    run('chroot /tmp/rootimg ssh-keygen -t rsa1 -N "" -C "ssh_host_rsa_key" -f /etc/ssh/ssh_host_rsa_key')
    run('chroot /tmp/rootimg ssh-keygen -t dsa -N "" -C "ssh_host_dsa_key" -f /etc/ssh/ssh_host_dsa_key')
    file = '/tmp/rootimg/root/.ssh/authorized_keys'
    for key in livecd['pubkeys']:
        files.append(file, '%s' % livecd['pubkeys'][key])
    run('chmod 640 %s' % file)
    run('umount /tmp/rootimg/proc /tmp/rootimg/sys /tmp/rootimg/dev')
    run('mksquashfs /tmp/rootimg /tmp/imgdir/live/filesystem.squashfs -noappend')
    put('live/menu.cfg', '/tmp/imgdir/isolinux/menu.cfg')
    with cd('/tmp/imgdir'):
        run('rm -f md5sum.txt')
        run('find -type f -print0 | xargs -0 md5sum | \
                grep -v isolinux/boot.cat | tee md5sum.txt')
        run('mkisofs -D -r -V "Teefaa Messenger" -cache-inodes \
                -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat \
                -no-emul-boot -boot-load-size 4 -boot-info-table \
                -o /tmp/%s.iso .' % livecd_name)
    get('/tmp/%s.iso' % livecd_name, livecd['saveto'])

@task
def make_pxeimage(pxename, pxecfg='cfg/pxe.yaml'):
    ''':pxename=XXXXX,pxecfg=cfg/pxeimage.yaml'''
    f = open(pxecfg)
    pxecfg = yaml.safe_load(f)[pxename]
    prefix = pxecfg['prefix']
    f.close()

    #put(pxecfg['livecd'], '/tmp/livecd.iso')
    if not file_is_dir('/mnt/tfmnt'):
        run('mkdir /mnt/tfmnt')
    run('mount /tmp/livecd.iso /mnt/tfmnt -o loop')
    expdir = prefix['export']
    if not file_is_dir(expdir):
        run('mkdir -p %s' % expdir)
    run('rsync -a --stats /mnt/tfmnt/ %s/%s' % (expdir, pxename))
    run('umount /mnt/tfmnt')
    tftpdir = prefix['tftpdir']
    if not file_is_dir('%s/%s' % (tftpdir, pxename)):
        run('mkdir -p %s/%s' % (tftpdir, pxename))
    run('cp %s/%s/live/initrd.img %s/%s/initrd.img' \
                % (expdir, pxename, tftpdir, pxename))
    run('cp %s/%s/live/vmlinuz %s/%s/vmlinuz' \
                % (expdir, pxename, tftpdir, pxename))
    pxefile = '%s/%s' % (prefix['pxelinux_cfg'], pxename)
    put('live/pxefile', pxefile)
    files.sed(pxefile, 'PXENAME', pxename)
    files.sed(pxefile, 'EXPDIR', expdir)
    files.sed(pxefile, 'PXESERVER', pxecfg['nfs_ip'])

@task
def mksnapshot(name, saveto):
    ''':name=XXXXX,saveto=XXXXX | Make Snapshot'''
    today = datetime.date.today
    distro = run('python -c "import platform; print platform.dist()[0].lower()"')
    print distro
    if distro == 'centos' or \
            distro == 'redhat':
        package_ensure_yum('squashfs-tools')
    elif distro == 'ubuntu' or \
            distro == 'debian':
        package_ensure_apt('squashfs-tools')
    else:
        print 'ERROR: distro %s is not supported.' % distro
        exit(1)
    workdir = '/root/TFROOTIMG-%s' % today()
    run('mkdir -p %s' % workdir)
    run('rsync -a --stats --one-file-system --exclude=%s / %s' \
            % (workdir.lstrip('/'), workdir))
    run('rsync -a --stats --one-file-system /var/ %s/var' \
            % workdir)
    run('rsync -a --stats --one-file-system /boot/ %s/boot' \
            % workdir)
    run('mksquashfs %s /tmp/%s-%s.squashfs -noappend' \
            % (workdir, name, today()))
    get('/tmp/%s-%s.squashfs' % (name, today()), \
            '%s/%s-%s.squashfs' % (saveto, name, today()))
    run('rm -rf %s' % workdir)
    run('rm -f /tmp/%s-%s.squashfs' % (name, today()))

@task
def hello():
    '''| Check if remote hosts are reachable.'''
    run('hostname')
    run('ls -la')

@task
def imagelist(imagesfile="ymlfile/scratch/images.yml"):
    '''| Show Image List'''
    f = open(imagesfile)
    images = yaml.safe_load(f)
    f.close()
    
    no = 1
    for image in images:
        print "%s. %s" % (no, image)
        no += 1

def read_ymlfile(ymlfile):
    '''Read YAML file'''

    if not os.path.exists(ymlfile):
        print ''
        print ' %s doesn\'t exist.' % ymlfile
        print ''
        exit(1)

    f = open(ymlfile)
    yml = yaml.safe_load(f)
    f.close()

    return yml

def check_distro():
    distro = run('python -c "import platform; print platform.dist()[0].lower()"')

    return distro
