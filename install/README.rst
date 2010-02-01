This is the main installer and it is assumed you are doing a server install, or on a VMWare/KVM/EC2.   As Demisauce is meant to be services used by your app, the recommended install is in vm/kvm/ec2 for development, not onto your actual machine. 

Simple Workflow:  Setup a KVM/VM/EC2 image for trial of Demisauce
===============================================================================
If you are doing this to try out, there is a bootstrap installer (install.sh) that will install with all default configuration allowing you to try it out.  If you want to adjust the configuration more you will need to install `Fabric <http://docs.fabfile.org>`_.  


I find the easiest vm install is to use VMBuilder for KVM on Ubuntu. Run this command to create a new kvm ubuntu machine and you are ready.  Update path, passwords, proxy server (ip address below) etc.  More info `At Ubuntu <https://help.ubuntu.com/9.10/serverguide/C/jeos-and-vmbuilder.html>`_::

    sudo vmbuilder kvm ubuntu --suite karmic --flavour virtual \
        --arch i386 -o --mem=512 \
        --libvirt qemu:///system --bridge=br0 \
        --user demisauce --name Demisauce --pass demisauce \
        --addpkg openssh-server --addpkg git-core \
        --mirror http://192.168.1.4:9999/ubuntu --tmpfs -  \
        --hostname=demisauce1 --dest ~/vm/demisauce1
    sudo virsh -c qemu:///system
    start demisauce1

If doing local VMWare install, Get `Ubuntu Server <http://www.ubuntu.com/getubuntu/download-server>`_ and start the install by doing updates and adding SSH and wget.  This also prints out the IP address (use bridging in vm if you want access via web from your desktop)::

    sudo apt-get update
    sudo apt-get install wget openssh-server 

If running on EC2, you can run an EC2 instance, create a volume, and attach it to instance.  To use on EC2 you will need to install `Fabric <http://docs.fabfile.org>`_ modify info in demisauce/install/fabfile.py and run::

    fab ec2 build_ec2


Now that you have a KVM/EC2/VM machine Logon and run the bootstrap installer or see next step for full configuration::

    cd tmp
    wget http://github.com/araddon/demisauce/raw/master/install/install.sh
    sudo chmod +x install.sh
    # install.sh mysql_root_pwd mysql_user_pwd role
    sudo ./install.sh
    
    
**Full installation**  `Get Demisauce <http://github.com/araddon/demisauce>`_,  Install `Fabric <http://docs.fabfile.org>`_ and edit the Fab files at /demisauce/install/fabfile.py and then install::

    fab d3 all:mysql_root_pwd="demisauce",mysql_user_pwd="demisauce"


Full Lifecycle Workflow:  Setup, dev, test, prod, deploy, repeat
================================================================
Follow steps above to get appliance image created.  

**1. Build Base Image (Dev, Test, Prod)**
    Build a machine from Scratch (see #2 for upgrades), you need to do the one step manually because it times out quite often::
    
        fab d1 build:mysql_root_pwd="demisauce",mysql_user_pwd="demisauce" -p demisauce


**2. Deploy Latest code to your env (Dev, Test, Prod)**
    Get latest set of source code, and potentially DB changes to deploy to Dev, Test or Prod machine(s). Note, this does *Not* include db script updates (see below)::
        
        fab d1 release:mysql_user_pwd="demisauce" -p demisauce

**3. Backup DB on Prod Machine**
    Backup/Copies of prod data for backup as well as usage on #4.  Combination of EC2 EBS as well as sql backups::
    
    fab d1 db_backup_apply -p demisauce

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
