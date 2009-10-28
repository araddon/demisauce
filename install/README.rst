This is the main installer and it is assumed you are doing a server install, or on a VMWare.   As Demisauce is meant to be services used by your app, the recommended install is in vm/kvm/xen for development, not onto your actual machine.  If you install on VM in dev you can setup your desktop dev machine configs to point to this image for Memcached, Redis, Gearman, MySQL etc and do python on your desktop.



Simple Workflow:  Setup a VM/EC2 image for trial of Demisauce
===============================================================
This uses `Fabric <http://docs.fabfile.org>`_  for installation download and install.


If doing local VM install, Get `Ubuntu Server <http://www.ubuntu.com/getubuntu/download-server>`_ and start the install by doing updates and adding SSH and wget.  This also prints out the IP address (use bridging in vm if you want access via web from your desktop)::

    apt-get update
    apt-get install openssh-server wget
    ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}

Download `Demisauce Source <http://github.com/araddon/demisauce>`_  using `git <http://git-scm.com/>`_ ::

    git clone git://github.com/araddon/demisauce.git
    
Edit the Fab files for your IP addresses of VM and run the install on VM:

    fab vm106 build_all:ospwd="demisauce",dbpwd="demisauce" -p demisauce


Full Lifecycle Workflow:  Setup, dev, test, prod, deploy, repeat
================================================================
Follow steps in Simple Worflow to install Fabric, and download
VM's for dev on local.   

**1. Build Base Image (Dev, Test, Prod)**
    Build a machine from Scratch (see #2 for upgrades), you need to do the one step manually because it times out quite often::
    
        fab vm107 build_step1:rootmysqlpwd="demisauce",userdbpwd="demisauce" -p demisauce
        apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1C73E014
        fab vm107 build_step2:rootmysqlpwd="demisauce",userdbpwd="demisauce" -p demisauce

**2. Deploy Latest code to your env (Dev, Test, Prod)**
    Get latest set of source code, and potentially DB changes to deploy to Dev, Test or Prod machine(s). Note, this does *Not* include db script updates (see below)::
        
        fab vm107 release:userdbpwd="demisauce" -p demisauce

**3. Backup DB on Prod Machine**
    Backup/Copies of prod data for backup as well as usage on #4.  Combination of EC2 EBS as well as sql backups.  

**4. Restore Prod Data on Dev, Test for testing next release**
    Getting your prod data onto machine to verify next release 
    will work.   

**5. Apply DB Script updates for latest release**
    After restoring a copy of prod date (optional), apply any db changes since last release.

**6. Test/Verify**
    Verify that changes work

**7. Linse, Lather, Repeat:  Do on prod after test**
    Repeat the steps for the dev, test, prod environments

**8. Take image of EC2 Prod machine**
    After building a machine (#1) and deploying code and data (#2,5) if you are on EC2 save a copy of machine to S3.
    
    This is useful in case you need to quickly restart a machine on failure (needs monitoring) OR for adding load balanced capacity.
