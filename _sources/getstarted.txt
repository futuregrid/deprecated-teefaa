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

This example provision Ubuntu-12.10 on two nodes. 
