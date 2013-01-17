Get Started
=====

The beta version of FG Teefaa is installed on india. If you have your FutureGrid account,
you can get bare-metal nodes like you get instance on Cloud. We use Torque Resource Manager
to schedule the provisioning. Here's how to do.

Login to india.futuregrid.org ::

 ssh username@india.futuregrid.org

Write the teefaa_userrc ::

 # Provide project_id and token.
 PROJECT_ID="fg-296"

 # Define reservation period in hours. 168(7days) is the maximum.
 HOURS=1

 # If you have your own costom image source, plovide the list.
 # If not, pick a image type from the choise and uncomment it.
 #IMAGE_LIST=$HOME/teefaa/image.list
 #IMAGE_NAME=your-custome on your image.list

 # Here's base image we have.
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
