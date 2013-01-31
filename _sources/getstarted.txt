GETTING STARTED
============

The current version of FG Teefaa is installed on the FutureGrid
resource india.futureGrid.org. If you have your FutureGrid account,
you can get bare-metal nodes just like you get instance on Cloud. At
We use the resource manager torque to manage and schedule a
provisioning. Thus a resource can be easily reprovisioned with the
qsub command.

To illustrate the use of FG teefaa we have chosen a simple example
that provisions the Ubuntu-12.10 on two nodes of india for 5
hours.

To achieve this, you must first login to india.futuregrid.org ::

 ssh username@india.futuregrid.org

Configuration
-----------

Next you need to define a FG teefaa configuration file. We are
providing here a simple example and assume the file is named as teefaa_userrc ::

 # Provide the FG project_id. 
 PROJECT_ID="fg-296"
 
 # Define the reservation period in hours. 
 # Currently 168 (e.g. 7 days) is the maximum.
 HOURS=5
 
 # If you have your own costom image source, provide it next.
 # If not, pick a image type from the choise and uncomment it.
 #IMAGE_LIST=$HOME/teefaa/image.list
 #IMAGE_NAME=your-custome on your image.list
 
 # The list of sample images includes.
 IMAGE_NAME=ubuntu-12.10
 #IMAGE_NAME=centos-6.3
 
 # specify your public key
 SSH_PUBKEYS="ssh-dss AAAAB....3NzaC.....1k/c..3MAGA...ACGEGAMlk sampleuser@example.edu"
 
 # Define a partitioning type.
 #PARTITION_TYPE="mbr"
 # NOTE: GPT in Teefaa is only available for Ubuntu and Debian right now.
 PARTITION_TYPE="gpt" 
 
 # Define disk setting.
 disk=sda
 sda1=(1 bios_grub none)
 sda2=(2 swap none)
 sda3=(50 ext4 "/")
 sda4=(900 xfs "/var/lib/nova")
 sda5=(-1 none none)

Provisioning 
------------
Next you need to define a provisioning script that gets scheduled with
the help of the queing system. For this example we name the file provision.pbs ::

 #!/bin/sh
 #
 # This is an example job script.
 #
 #PBS -N PROVISIONING
 #PBS -l nodes=2:ppn=8
 #PBS -q provision
 #PBS -M sampleuser@example.edu
 #PBS -m abe

 module load torque

 # Set the path to your teefaa_localrc
 USERRC=~/jobs/teefaa_userrc

 # Tell if you need a subnet for building your Cloud Infrastructure.
 # (yes/no)
 NEED_SUBNET=yes

 #####  PLEASE DO NOT CAHANGE THE FOLLOWING LINES  #####
 sleep 10
 # Pass your rc file to Teefaa Messenger via /tmp
 pbsdsh cp $USERRC /tmp/userrc
 sleep 10

This file is used to submit the job. ::
 
 [sampleuser@i136]$ qsub provision.pbs

The job will reserve two nodes, setup the provisioning configuration
and then reboot the machines according to the information from our
configuration file. During the execution of this job, the nodes will
boot with a customized netboot image, then install Ubuntu-12.10, and
then reboot. It will take about 10 to 15 minutes to finish the
installation.  Once the nodes are ready, they will show up on our FG
dispather queue which is installed on the node i132 on india.  You can
check the status of your activities as follows::

 qstat @i132
 [sampleuser@i136]$ qstat @i132
 Job id                    Name             User            Time Use S Queue
 ------------------------- ---------------- --------------- -------- - -----
 28.i132                    i6_sampleuser      tfadmin         00:00:00 R dispatch       
 29.i132                    i51_sampleuser     tfadmin         00:00:00 R dispatch

In this example, teh user *sampleuser* got i6 and i51. Now the user
can login to them as root. ::

 [sampleuser@i136]$ ssh root@i6 # or i6r.idp.iu.futuregrid.org if you access from external.
 Welcome to Ubuntu 12.10 (GNU/Linux 3.5.0-21-generic x86_64)

  * Documentation:  https://help.ubuntu.com/

   System information as of Wed Jan 16 23:27:09 EST 2013

   System load:  0.0               Processes:           111
   Usage of /:   2.7% of 49.22GB   Users logged in:     0
   Memory usage: 0%                IP address for eth0: 172.29.200.6
   Swap usage:   0%                IP address for eth1: 149.165.146.6

   Graph this data and manage this system at https://landscape.canonical.com/

 Last login: Wed Jan 16 22:58:11 2013 from i136.idpm
 root@i6:~#

If you want to check how long you used your instances, you can check the time with this command. ::

  [sampleuser@i136]$ qstat -f 29.i132 | grep resources_used.walltime
    resources_used.walltime = 02:16:08

This example shows the used-time of Job id 29 on Dispatcher
queue. Here it indicates that it spent 2 hours 16 minutes 8
seconds. Remember that the nodes are available for 5 hours.

Now you can test your software or some opensource system on the two bare-metal nodes.

The next section shows how to build OpenStack Folsom, and then shows how to clone 
the nova-compute to another bare-metal node.

Build OpenStack Folsom on the two nodes
---------------------------------------------------

First of all, please check the output file of your provisioning.pbs. If you used my
template the output is on PROVISIONING.oxxxx. This time I got PROVISIONING.o564346. ::

  [sampleuser@i136]$ cat PROVISIONING.o564346
  ncpus=1,neednodes=2:ppn=8,nodes=2:ppn=8,walltime=00:30:00

  You can use 192.168.101/24 for your Cloud instances

So you can use 192.168.101/24 for your OpenStack instances.

To make this section shorter, let us use scripts to install openstack controller.
Thi example build controller on node i6 ::

  [sampleuser@i136]$ git clone https://github.com/kjtanaka/deploy_folsom.git
  [sampleuser@i136]$ cp deploy_folsom/setuprc-example deploy_folsom/setuprc
  [sampleuser@i136]$ vi deploy_folsom/setuprc
  # setuprc - configuration file for deploying OpenStack

  # 
  # 1. Set the password.
  #
  PASSWORD="DoNotMakeThisEasy"
  export ADMIN_PASSWORD=$PASSWORD
  export SERVICE_PASSWORD=$PASSWORD
  export ENABLE_ENDPOINTS=1
  MYSQLPASS=$PASSWORD
  QPID_PASS=$PASSWORD
  #
  # 2. Set your controller IP Address. In this example, 
  #    it's node i6's IP Address.
  CONTROLLER="149.165.146.6"
  #
  # 3. Set The subnet you got on PROVISIONING.oxxxx
  #    This example I got 192.168.101.0/24 as showen
  #    above.
  FIXED_RANGE="192.168.101.0/24"
  #
  # 4. Many example of OpenStack put this as "%",
  #    but I think it's too open, so please set it
  #    as "149.165.146.%".
  MYSQL_ACCESS="149.165.146.%"
  PUBLIC_INTERFACE="eth1"
  FLAT_INTERFACE="eth0"

Then, copy the folder to node i6 and execute setup_controller.sh, and copy it to 
node i51 and execute setup_compute.sh ::

  [sampleuser@i136]$ scp -r deploy_folsom i6:deploy_folsom
  [sampleuser@i136]$ ssh root@i6 "cd deploy_folsom; bash -ex setup_controller.sh"
  [sampleuser@i136]$ scp -r deploy_folsom i52:deploy_folsom
  [sampleuser@i136]$ ssh root@i51 "cd deploy_folsom; bash -ex setup_controller.sh"

The nodes are rebooted at the end. So login to the controller node i6 when the machine
is up online. Then run your first instance. ::

   [sampleuser@i136]$ ssh root@i6
   root@i6:~# cd deploy_folsom
   root@i6:~# . admin_credential
   root@i6:~# nova boot --image ubuntu-12.10 --flavor 1 --key-name key1 vm001
   root@i6:~# nova list
   +--------------------------------------+-------+--------+-----------------------+
   | ID                                   | Name  | Status | Networks              |
   +--------------------------------------+-------+--------+-----------------------+
   | 1183b8ea-253e-4c03-afe6-6df2a66854fd | vm001 | ACTIVE | private=192.168.101.2 |
   +--------------------------------------+-------+--------+-----------------------+

Somehow first one or two instance(s) tend to end up with "ERROR" Status. If it happens
to you too, please delete them and run new instance. Once your instance become "ACTIVE"
you should be able to login as "ubuntu" like this. ::
   
   root@i6:~# ssh -i key1.pem ubuntu@192.168.101.2

Create another nova-compute from running node
----------------------------------------------------

This section shows you how to create a snapshot of nova-compute node, and copy it to another node.
The process is a bit a lot so here's description of the process.

#. Delete your instances and disable the nova-compute service.
#. Create a snapshot.
#. Create a host(VM on OpenStack) for your image repository.
#. Upload your snapshot and mount it.
#. Modify your provisioning job and submit it.

Here I begin with i51 which is my compute node.

**Delete your instances and disable the nova-compute service.**

First of all, make sure you delete running instances, and disable the 
nova-compute service on i51. ::
   
   root@i6:~# nova delete vm001
   root@i6:~# nova delete vm002
     :
     : Delete instances on i51...
     :
   root@i6:~# nova-manage service disable --host i51 --service nova-compute
   root@i6:~# nova-manage service list

**Create a snapshot.**

Download Teefaa. ::
   
   root@i51:~# git clone https://github.com/futuregrid/teefaa.git
   root@i51:~# cd teefaa

Create your snapshotrc. ::

   root@i51:~# cp snapshotrc-example snapshotrc
   root@i51:~# vi snapshotrc
   # snapshotrc

   SNAPSHOT_DIR="/var/lib/teefaa/snapshot"

   # Define logfile.
   LOGFILE=/tmp/snapshot.log

   # Define the file of exclude list.
   EXCLUDE_LIST=$TOP_DIR/exclude.list

Create your exclude.list and add "var/lib/nova/instances/*" ::

   root@i51:~# cp exclude.list-example exclude.list
   root@i51:~# vi exclude.list
   proc/*
   sys/*
   dev/*
   tmp/*
   mnt/*
   media/*
   lost+found
   var/lib/nova/instances/*

Execute snapshot.sh. ::

   root@i51:~# ./snapshot.sh

If you get error because of necessary package, install tree, xfsprogs and squashfs-tools like this. ::

   root@i51:~# apt-get install tree xfsprogs squashfs-tools

The snapshot will be created in /var/lib/teefaa/snapshot .
