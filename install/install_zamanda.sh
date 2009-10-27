#!/usr/bin/env bash
# 
#  chmod +x install_zamanda.sh
#  usage:   $install_zamanda.sh mysql_root_password  demisauce_mysql_pwd  vm
#
# ----------------------------------------------------------------------------
# Password locations:
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
    read MYSQL_ROOT_PWD
    if [ "$MYSQL_ROOT_PWD" = "" ] ; then
        MYSQL_ROOT_PWD="demisauce"
    fi
    read DEMISAUCE_MYSQL_PWD
    if [ "$DEMISAUCE_MYSQL_PWD" = "" ] ; then
        DEMISAUCE_MYSQL_PWD="demisauce"
    fi
    read vmorec2
    if [ "$vmorec2" != "" ] ; then
        VMOREC2=$vmorec2
    fi
}

#------- Start of program
DEMISAUCE_HOME='/home/demisauce'
MYSQL_HOME='/vol/lib'
ZRM_HOME='/vol/mysql-zrm'
DEMISAUCE_WEB_HOME=$DEMISAUCE_HOME/current_web
VMOREC2="ec2"
SERVER_ROLE='all'

checkRoot
if [ $# -eq "0" ] ; then
    askArgs
else 
    MYSQL_ROOT_PWD=$1
    DEMISAUCE_MYSQL_PWD=$2
    VMOREC2=$3
fi

mkdir -p /vol/mysql-zrm

# install zamanda backup , zamanda depends on mailx
echo "----  Installing Zamanda Backup for MySql, needs mailx for sending emails"
apt-get --yes --force-yes -q install mailx libxml-parser-perl libdbd-mysql-perl
# if no mail transport agent defined mailx dependency will get one here
apt-get -f install 
cd /tmp
wget http://www.zmanda.com/downloads/community/ZRM-MySQL/2.1.1/Debian/mysql-zrm_2.1.1_all.deb
dpkg -i mysql-zrm*.deb 
rm mysql-zrm*.deb 
# change from /var/lib/mysql-zrm to $ZRM_HOME
escaped_zrm_home="${ZRM_HOME//\//\/}"
echo "----changing ZRM backup root to:  $escaped_zrm_home "
perl -pi -e "s/\#destination=\/var\/lib\/mysql\-zrm/$escaped_zrm_home/g" /etc/mysql-zrm/mysql-zrm.conf || die "could not change mysql-zrm.conf"

mkdir -p "/etc/mysql-zrm/demisauce"
cat <<EOL > /etc/mysql-zrm/demisauce/mysql-zrm.conf
host="localhost"
databases="demisauce"
password="$MYSQL_ROOT_PWD"
user="backup-user"
compress=1
mysql-binlog-path="$MYSQL_HOME"
EOL
chown mysql:mysql "/etc/mysql-zrm/demisauce"
chown mysql:mysql "/etc/mysql-zrm/demisauce/mysql-zrm.conf"
/etc/init.d/mysql start



