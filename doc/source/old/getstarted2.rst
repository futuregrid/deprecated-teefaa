GETTING STARTED
============

Install
-------

Download from github, install and create config file::
   
  [root@yourhost]# git clone git@github.com:futuregrid/teefaa.git
  [root@yourhost]# python setup.py install
  [root@yourhost]# mkdir ~/.teefaa
  [root@yourhost]# cp etc/teefaa.conf-example ~/.teefaa/teefaa.conf

Create a snapshot of your machine
---------------------------------

To make snapshot::

  [root@yourhost]# teefaa create-snapshot

The snapshot will be created on /var/lib/teefaa/snapshots. 
If you want to change the directory, modify your teefaa.conf

Create a repository of your machine
-----------------------------------

To create repository on india, send your snapshot to india.futuregrid.org,
and then login to india.::

    scp /var/lib/teefaa/snapshots/your-snapshot.squashfs youraccount@india.futuregrid.org:
    ssh youraccount@india.futuregrid.org

Then, load python module, make sure you have access to our OpenStack,
and then execute teefaa create repo, like this.::

    module load teefaa
    euca-describe-instances
    teefaa create-repo --snapshot your-snapshot.squashfs

You will get output like this.::

    here's output.

Boot your image
---------------

To boot your image, execute this command::

    teefaa boot --repo <your repository> \
                --number <number of nodes> \
                --queue <name of queue> \
                --hours <reservation hours(<168)>

Here's an example to reserve 2 nodes on india for 48 hours(2 days)::

    teefaa boot --repo 10.1.2.129:/mnt/tikgjE9g8 \
                --number 2
                --queue provision
                --hours 48

In about 10~15 minutes, your reservation show up on dispatcher's queue, which is i132 on india.
You can check it by this command.::

    qsub @i132

If your nodes are on the list, you should be able to login the nodes as root.
