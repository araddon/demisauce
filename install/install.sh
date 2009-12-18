#!/usr/bin/env bash
# 
#  chmod +x install.sh
#  usage:   $install.sh mysql_root_password  demisauce_mysql_pwd role(all|web|db|memcached)
#
#  Starting from this base:   
#       apt-get update
#       apt-get install openssh-server wget
#  If VMWare:
#       execute the install_openvmtools.sh script first
# ----------------------------------------------------------------------------
#  TODO
#   - consider changing log level in apache2/sites-available/default
#   - other than ubuntu (move to puppet/capistrano?)
#   - security hardening:  https://help.ubuntu.com/community/Security
# ----------------------------------------------------------------------------
# Password locations:
#  - /home/demisauce/current_web/production.ini (mysql)
#  - /etc/mysql-zrm/demisauce/mysql-zrm.conf  (mysql-backup pwd)
function die
{
    echo $*
    exit 1
}
function checkRoot
{
    if [ ! $( id -u ) -eq 0 ]; then
        die "Must have super-user rights to run this script.  Run with the command 'sudo $0'"
    fi
}
# Get all arguments if not supplied
function askArgs
{
    echo -en "Please enter your MySQL root password: or 
return to accept [demisauce]"
    read MYSQL_ROOT_PWD
    if [ "$MYSQL_ROOT_PWD" = "" ] ; then
        MYSQL_ROOT_PWD="demisauce"
    fi
    echo -en "Please enter password for the MySQL password for the demisauce web app or
return to accept [demisauce]"
    read DEMISAUCE_MYSQL_PWD
    if [ "$DEMISAUCE_MYSQL_PWD" = "" ] ; then
        DEMISAUCE_MYSQL_PWD="demisauce"
    fi
    echo -en "Please enter 'ec2' or 'vm' 
    return to accept:  'vm'   :   "
    read vmorec2
    if [ "$vmorec2" != "" ] ; then
        VMOREC2=$vmorec2
    fi
    echo -en "Please enter password for the root password to run sudo
return to accept [demisauce]"
    read ROOT_PWD
    if [ "$ROOT_PWD" = "" ] ; then
        ROOT_PWD="demisauce"
    fi
}

#-----------------------------------  Start of program
DEMISAUCE_HOME='/home/demisauce'
MYSQL_HOME='/vol/lib'
ZRM_HOME='/vol/mysql-zrm'
DEMISAUCE_WEB_HOME=$DEMISAUCE_HOME/current_web
VMOREC2="vm"

checkRoot
askArgs

mkdir -p $DEMISAUCE_HOME/lib
cd /tmp
# Upgrade/install packages
apt-get -y update
# some basics
echo "----  installing build-essentials-----"
apt-get install --yes --force-yes -q build-essential
echo "----  installing ssh server, wget, cron, rsync, unzip -----"
apt-get install --yes --force-yes -q openssh-server  wget unzip cron rsync 
echo "----  installing git-core ------------"
apt-get install --yes --force-yes -q git-core
echo "----  installing python tools -----"
apt-get install --yes --force-yes -q python-dev python-setuptools
easy_install simplejson
cd $DEMISAUCE_HOME/lib
git clone git://github.com/bitprophet/fabric.git
pip install pycrypto
cd fabric
python setup.py install
# IP="$(wget -o/dev/null -O- http://jackson.io/ip/)"
# http://jackson.io/ip/service.html
#TODO: this doesn't work on mac
#linux$  eth0   inet addr:192.168.0.106  Bcast:192.168.0.255  Mask:255.255.255.0
#mac$ en0   inet 192.168.0.101 netmask 0xffffff00 broadcast 192.168.0.255
HOSTNAME=`ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}'`

echo $HOSTNAME
#perl -pi -e "s/\/var\/lib\/mysql/$escaped_mysql_home/g" /etc/mysql/my.cnf || die "could not change my.cnf"
mkdir -p $DEMISAUCE_HOME/src
cd $DEMISAUCE_HOME/src
git clone git://github.com/araddon/demisauce.git
chown -R demisauce:demisauce /home/demisauce/src
cd /home/demisauce/src/demisauce/install
fab vmlocal build:rootmysqlpwd="$MYSQL_ROOT_PWD",userdbpwd="$DEMISAUCE_MYSQL_PWD",host="$HOSTNAME" -p $ROOT_PWD
fab vmlocal release:userdbpwd="$DEMISAUCE_MYSQL_PWD",host="$HOSTNAME" -p $ROOT_PWD


