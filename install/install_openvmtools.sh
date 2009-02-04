#!/bin/bash

OPEN_VM_TOOLS_VERSION="2009.01.21-142982"
OPEN_VM_TOOLS_MIRROR_PATH="http://internap.dl.sourceforge.net/sourceforge/open-vm-tools"

# Prior to running this script, you must attach the VMWare Tools iso to the cdrom drive.
# You can do this with VMWare Server (and other consoles) by selecting the "Install VMWare Tools" option.
# The script will mount the drive and extract the package.

function die()
{
    echo $*
    exit 1
}

function checkRoot()
{
    if [ ! $( id -u ) -eq 0 ]; then
        die "Must have super-user rights to run this script.  Run with the command 'sudo $0'"
    fi
}

function installPackages()
{
    for package in "$@"; do
        if [ -z `dpkg -l |grep $package` ]; then
            packages="$packages $package"
        fi
    done
    if [ ! -z "$packages" ]; then
        apt-get install -y --force-yes $packages
        if [ ! $? -eq 0 ]; then
            die "Script encountered an error during package installation.  Check errors and retry."
        fi
    fi
}

function checkDependencies()
{
    if [ -z "`dpkg -l |grep wget`" ]; then
        echo "Install script requires wget package.  Script will install package."
        packages="wget"
    fi
    if [ ! -x /usr/bin/killall ]; then
        echo "VMware tools requires 'killall'.  Script will install psmisc package"
        packages="$packages psmisc"
    fi
    installPackages $packages
}
# ----------
# Main script
# ----------

checkRoot
checkDependencies

if [ ! -d vmwaretools ]; then
    mkdir vmwaretools
fi
cd vmwaretools

wget -c $OPEN_VM_TOOLS_MIRROR_PATH/open-vm-tools-$OPEN_VM_TOOLS_VERSION.tar.gz
if [ ! $? -eq 0 ]; then
    die "Encountered error retrieving open-vm-tools tar ball.  Check messages and try again."
fi
echo -n "Extracting open-vm-tools tar ball..."
tar xfz open-vm-tools-$OPEN_VM_TOOLS_VERSION.tar.gz
if [ ! $? -eq 0 ]; then
    die "\nEncountered error extracting open-vm-tools.  Check messages and try again."
fi
echo

mount -t iso9660 -o ro /dev/scd0 /media/cdrom0
if [ ! $? -eq 0 ]; then
    die "Could not mount VMWare Tools image as cdrom.  Make sure you have setup the VMWare to install tools and try again."
fi
echo -n "Extracting VMwareTools tar ball..."
tar xfz /media/cdrom0/VMwareTools-*.tar.gz
if [ ! $? -eq 0 ]; then
    die "Encountered error extracting VMWareTools.  Check messages and try again."
fi
umount /media/cdrom0
echo

installPackages build-essential libproc-dev libicu-dev libdumbnet-dev linux-headers-`uname -r`

cd open-vm-tools-*
./configure --without-x
if [ ! $? -eq 0 ]; then
    die "Configuration of open-vm-tools was not successful.  Check errors for additional packages not installed by the script and try again."
fi
make
if [ ! $? -eq 0 ]; then
    die "Make of open-vm-tools was not successful.  Cannot continue."
fi

cd modules/linux
for i in *
do
    mv ${i} ${i}-only
    tar -cf ${i}.tar ${i}-only
done
cd ../../..

mv -f open-vm-tools-*/modules/linux/*.tar vmware-tools-distrib/lib/modules/source/

cd vmware-tools-distrib
./vmware-install.pl --default


