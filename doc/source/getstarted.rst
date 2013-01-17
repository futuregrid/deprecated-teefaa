Get Started
=====

The beta version of FG Teefaa is installed on india. If you have your FutureGrid account,
you can get bare-metal nodes like you get instance on Cloud. We use Torque Resource Manager
to schedule the provisioning. 

Here's an example which provision Ubuntu-12.10 on two bare-metal nodes in india for 5 hours
as if you get 2 instances on Cloud.

Login to india.futuregrid.org ::

 ssh username@india.futuregrid.org

Write your teefaa_userrc ::

 # Provide project_id and token.
 PROJECT_ID="fg-296"

 # Define reservation period in hours. 168(7days) is the maximum.
 HOURS=5

 # If you have your own costom image source, plovide the list.
 # If not, pick a image type from the choise and uncomment it.
 #IMAGE_LIST=$HOME/teefaa/image.list
 #IMAGE_NAME=your-custome on your image.list

 # Here's basic images we have.
 IMAGE_NAME=ubuntu-12.10
 #IMAGE_NAME=centos-6.3

 # Define ssh public key
 SSH_PUBKEYS="ssh-dss AAAAB....3NzaC.....1k/c..3MAGA...ACGEGAMlk you@macbook"

 # Define partitioning type.
 PARTITION_TYPE="mbr"
 # GPT in Teefaa is only available for Ubuntu and Debian right now.
 #PARTITION_TYPE="gpt" 

 # Define disk setting.
 disk=sda
 sda1=(2 swap none)
 sda2=(50 ext4 "/")
 sda3=(-1 xfs "/data")

Write your provision job file. Here's example, I name the file as provision.pbs ::

 #!/bin/sh
 #
 # This is an example job script.
 #
 #PBS -N PROVISIONING
 #PBS -l nodes=2:ppn=8
 #PBS -q provision
 #PBS -M username@examle.edu
 #PBS -m abe

 module load torque

 # Set the path to your teefaa_localrc
 USERRC=~/jobs/teefaa_userrc

 #####  DON'T CHANGE BELOW  #####
 sleep 10
 # Pass your rc file to Teefaa Messenger via /tmp
 pbsdsh cp $USERRC /tmp/userrc
 sleep 10

Then, submit the job. ::
 
 qsub provision.pbs

The job will get two nodes, setup the provisioning configuration and then reboot the machines.
After the job finishes, the nodes will boot with Teefaa Messenger(customized netboot image.), then
install Ubuntu-12.10 then reboot. It will take about 10 to 15 minutes to finish the installation.
Once the nodes are ready, they will show up on Dispather queue. Now the queue is on the node i132,
You can check it with this command. ::

 qstat @i132
 [ktanaka@i136 jobs]$ qstat @i132
 Job id                    Name             User            Time Use S Queue
 ------------------------- ---------------- --------------- -------- - -----
 28.i132                    i6_ktanaka       tfadmin         00:00:00 R dispatch       
 29.i132                    i51_ktanaka      tfadmin         00:00:00 R dispatch

In this example, I got i6 and i51. So I should be able to login to them as root. ::

 [ktanaka@i136 jobs]$ ssh root@i6
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

If you want to check how long you spent, you can check the time with this command. ::

  [ktanaka@i136 jobs]$ qstat -f 29.i132 | grep resources_used.walltime
    resources_used.walltime = 02:16:08

This example shows the used-time of Job id 29 on Dispatcher queue. 
I spent 2 hours 16 minutes 8 seconds. These nodes are available for 5 hours.

In the next section, I'll explain how to create your custom images and the list.
