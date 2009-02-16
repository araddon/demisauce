#!/usr/bin/env bash
#
# install Func (and certmaster if master)
#   https://fedorahosted.org/func/
#
# TODO:  separate these or allow override as certmaster
#           isn't need on slaves
# -----------------------------------------------------
ENV="dev"

# http://ubuntu-tutorials.com/2007/11/13/service-tool-available-on-ubuntu-710/
# http://ubuntuforums.org/archive/index.php/t-20583.html
apt-get install --yes --force-yes -q openssl sysvconfig sysv-rc-conf
easy_install pyopenssl

cd /tmp
#for some reason the make install of git repository doesn't install certmaster?
wget http://people.fedoraproject.org/~alikins/files/certmaster/certmaster-0.24.tar.gz
tar -xzvf certmaster*.tar.gz
rm cert*.tar.gz
cd cert*
python setup.py install
cd /tmp
rm -rf certmaster-* 

if [ $ENV = "dev" ] ; then
    cd /home/demisauce
    apt-get install --yes --force-yes -q make
    git clone git://github.com/araddon/func.git 
    make install
else
    wget http://people.fedoraproject.org/~alikins/files/func/func-0.24.tar.gz
    tar -xzvf func*.tar.gz
    rm func*.tar.gz
    cd func*
    python setup.py install
    cd /tmp
    rm -rf func-*
    #make install
fi

# edit the /etc/certmaster/minion.conf to name of certmaster?
#perl -pi -e s/Deny\ from\ all/\#Deny\ from\ all/g /etc/certmaster/minion.conf || echo ""
# or edit /etc/hosts to add name of certmaster if this box?  
# /etc/init.d/networking restart

# start certmaster:
#/etc/init.d/certmaster start
update-rc.d certmaster defaults
invoke-rc.d certmaster start

update-rc.d funcd defaults
invoke-rc.d funcd start

