.. Cloud Metrics documentation master file, created by
   sphinx-quickstart on Tue Apr 10 10:11:26 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the FG Teefaa documentation
=========================================
FutureGrid Teefaa is a set of scripts which consists of Snapshot,
Clouimg, Bootstrap and Torque Plugin.

* Snapshot - Makes a snapshot of an OS and compresses it.
* Cloudimg - Makes a cloud image from a snapshot.
* Bootstrap - Installs a system from a snapshot, a running system or a running instance.
* Torque Plugin - Provides cluster users to provision OS images on compute nodes.

The goal of FG Teefaa is to provide the scripts and methods to easily provision multiple 
Operation Systems at user's local enviromnent(Desktop, Laptop, VMs), at Cloud as instances and at 
Bare-metal Cluster as bare-metal hosts. 

The picture of FG Teefaa is like this. Users can start system development on 
a Desktop/Laptop/VM and make a snapshot for backup, then make cloud image for 
running the image on multiple instances, and then run it on bare-metal nodes.


Contents:

.. toctree::
   :maxdepth: 2

   getstarted
   intro
   modules
   download
   support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
