GETTING STARTED
============

The current version of FG Teefaa is installed on the FutureGrid
resource india.futureGrid.org. If you have your FutureGrid account,
you can get bare-metal nodes just like you get instance on Cloud. At
We use the resource manager torque to manage and schedule a
provisioning. Thus a resource can be easily reprovisioned with the
qsub command.

To illustrate the use of FG teefaa we have chosen a simple example
that provisions the OS Ubuntu-12.10 on two nodes of india for 5
hours. 

To achieve this, you must first login to india.futuregrid.org ::

 ssh username@india.futuregrid.org

Configuration
-----------

Next you need to define a FG teefa configuration file. We are
providing here a simple example and assume the file is located in teefaa_userrc ::

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
 SSH_PUBKEYS="ssh-dss AAAAB....3NzaC.....1k/c..3MAGA...ACGEGAMlk you@macbook"
 
 # Define a partitioning type.
 PARTITION_TYPE="mbr"
 # GPT in Teefaa is only available for Ubuntu and Debian right now.
 #PARTITION_TYPE="gpt" 
 
 # Define the disk device partitioning
 disk=sda
 sda1=(2 swap none)
 sda2=(50 ext4 "/")
 sda3=(-1 xfs "/data")

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
 #PBS -M username@example.edu
 #PBS -m abe

 module load torque

 # Set the path to your teefaa_localrc
 USERRC=~/jobs/teefaa_userrc

 #####  PLEASE DO NOT CAHANGE THE FOLLOWING LINES  #####
 sleep 10
 # Pass your rc file to Teefaa Messenger via /tmp
 pbsdsh cp $USERRC /tmp/userrc
 sleep 10

This file is used to submit the job. ::
 
 qsub provision.pbs

The job will reserve two nodes, setup the provisioning configuration
and then reboot the machines according to the information from our
configuration file. During the execution of this job, the nodes will
boot with a customized netboot image, then install Ubuntu-12.10, and
then reboot. It will take about 10 to 15 minutes to finish the
installation.  Once the nodes are ready, they will show up on our FG
dispather queue which is installed on the node i132 on india.  You can
check the status of your activities as follows::

 qstat @i132
 [sampleuser@i136 jobs]$ qstat @i132
 Job id                    Name             User            Time Use S Queue
 ------------------------- ---------------- --------------- -------- - -----
 28.i132                    i6_sampleuser       tfadmin         00:00:00 R dispatch       
 29.i132                    i51_sampleuser     tfadmin         00:00:00 R dispatch

In this example, teh user *sampleuser* got i6 and i51. Now the user
can login to them as root. ::

 [sampleuser@i136 jobs]$ ssh root@i6
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

  [sampleuser@i136 jobs]$ qstat -f 29.i132 | grep resources_used.walltime
    resources_used.walltime = 02:16:08

This example shows the used-time of Job id 29 on Dispatcher
queue. Here it indicates that it spent 2 hours 16 minutes 8
seconds. Remember that the nodes are available for 5 hours.

In the next section, we explain how to create your custom images.
