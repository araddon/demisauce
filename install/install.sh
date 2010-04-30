#!/usr/bin/env bash
# 
#  chmod +x install.sh
#  usage:   $install.sh \
#                 -m mysql_root_password  \ # mysql root pwd
#                 -p demisauce_mysql_pwd \  # mysql pwd to run app
#                 -i all \                  # role:   (solr|all)
#                 -r root_pwd               # pwd to do install via ssh
#
#  Starting from this base:   
#       apt-get update
#       apt-get install openssh-server
# ----------------------------------------------------------------------------
#  TODO
# ----------------------------------------------------------------------------
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
    echo -en "Please enter role:  solr, all
    return to accept:  'all'   :   "
    read serverrole
    if [ "$serverrole" != "" ] ; then
        SERVER_ROLE=$serverrole
    fi
    echo -en "Please enter password for the root user on vm to run sudo on vm
return to accept [demisauce]"
    read ROOT_PWD
    if [ "$ROOT_PWD" = "" ] ; then
        ROOT_PWD="demisauce"
    fi
}

#-----------------------------------  Start of program
DEMISAUCE_HOME='/home/demisauce'
SERVER_ROLE='all'
checkRoot
# IP="$(wget -o/dev/null -O- http://jackson.io/ip/)"
# http://jackson.io/ip/service.html
#TODO: this doesn't work on mac
#linux$  eth0   inet addr:192.168.0.106  Bcast:192.168.0.255  Mask:255.255.255.0
#mac$ en0   inet 192.168.0.101 netmask 0xffffff00 broadcast 192.168.0.255
HOSTNAME=`ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}'`

if [ $# -eq "0" ] ; then
    askArgs
else 
    while [ $# -gt 0 ]; do
        case $1 in
            -p) DEMISAUCE_MYSQL_PWD=$2;                         shift 2 ;;
            -m) MYSQL_ROOT_PWD=$2;                              shift 2 ;;
            -i) SERVER_ROLE=$2;                                 shift 2 ;;
            -r) ROOT_PWD=$2;                                    shift 2 ;;
            *)             echo "$0: Unrecognized option: $2" >&2; exit 1;
        esac
    done
fi
echo "========================================================================"
echo "Installing Demisauce; Role = $SERVER_ROLE to $DEMISAUCE_HOME host $HOSTNAME"
echo "========================================================================"

mkdir -p $DEMISAUCE_HOME/lib
cd /tmp
# Upgrade/install packages
apt-get -y update
# some basics
echo "----  installing build-essentials-----"
apt-get install --yes --force-yes -q build-essential
echo "----  installing ssh server, wget, cron, rsync, unzip -----"
apt-get install --yes --force-yes -q openssh-server  curl wget unzip cron rsync 
echo "----  installing git-core ------------"
apt-get install --yes --force-yes -q git-core
echo "----  installing python tools -----"
apt-get install --yes --force-yes -q python-dev python-setuptools

cd $DEMISAUCE_HOME/lib
git clone git://github.com/bitprophet/fabric.git
easy_install pycrypto
cd fabric
python setup.py install

#perl -pi -e "s/\/var\/lib\/mysql/$escaped_mysql_home/g" /etc/mysql/my.cnf || die "could not change my.cnf"
mkdir -p $DEMISAUCE_HOME/src
cd $DEMISAUCE_HOME/src
git clone git://github.com/araddon/demisauce.git
chown -R demisauce:demisauce /home/demisauce/src
cd /home/demisauce/src/demisauce/install
if [ $SERVER_ROLE = "all" ] ; then
  fab vmlocal build:mysql_root_pwd="$MYSQL_ROOT_PWD",mysql_user_pwd="$DEMISAUCE_MYSQL_PWD",host="$HOSTNAME",local=Tru -p $ROOT_PWD
  fab vmlocal release:mysql_user_pwd="$DEMISAUCE_MYSQL_PWD",host="$HOSTNAME" -p $ROOT_PWD
  fab vmlocal restart_web
fi
if [ $SERVER_ROLE = "solr" ] ; then
  fab vmlocal build_solr:host="$HOSTNAME" -p $ROOT_PWD
fi

