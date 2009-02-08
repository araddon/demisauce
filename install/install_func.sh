#!/usr/bin/env bash
#
# install Func (and certmaster if master)
#   https://fedorahosted.org/func/
#
# TODO:  separate these or allow override as certmaster
#           isn't need on slaves
# -----------------------------------------------------
cd /tmp
apt-get install openssl
easy_install pyopenssl
wget http://people.fedoraproject.org/~alikins/files/certmaster/certmaster-0.24.tar.gz
tar -xzvf certmaster*.tar.gz
rm cert*.tar.gz
cd cert*
python setup.py install
cd /tmp
rm -rf certmaster-*
wget http://people.fedoraproject.org/~alikins/files/func/func-0.24.tar.gz
tar -xzvf func*.tar.gz
rm func*.tar.gz
cd func*
python setup.py install
cd /tmp
rm -rf func-*
#make install


# start certmaster:
#/etc/init.d/certmaster start
update-rc.d certmaster defaults
invoke-rc.d certmaster start

# edit the minion.conf
update-rc.d funcd defaults
invoke-rc.d funcd start

