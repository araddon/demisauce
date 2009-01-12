This is the main installer and it is assumed you are doing a server install, or on a VMWare.   As Demisauce is meant to be services used by your app, the recommended install is in vm/kvm/xen for development, not onto your actual machine.  

Installation and Setup EC2 or Ubuntu VM
========================================
This installation uses Ubuntu JEOS

Get `Ubuntu JEOS <http://www.ubuntu.com/products/whatisubuntu/serveredition/jeos>`_ and start the install by doing updates and adding SSH and wget::

    apt-get update
    apt-get install openssh-server wget

Get `Demisauce Installer <http://github.com/araddon/demisauce/raw/master/install/install.sh>`_  using wget or just copy text.

Copy to /tmp/install.sh and run::

    cd /tmp
    wget http://github.com/araddon/demisauce/raw/master/install/install.sh
    chmod +x install.sh 
    ./install.sh

EC2 Install
===========
Assuming you have the  path/to/demisauce/install folder

Run this from a command line::

    python start_ec2.py amazon_access_key secret_access_key

