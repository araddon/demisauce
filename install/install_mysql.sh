#!/usr/bin/env bash
# 
#  chmod +x install.sh
#  usage:   $install.sh mysql_root_password  demisauce_mysql_pwd role(all|web|db|memcached) vm
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


echo "----   Starting MySQL install  ------------"
# suppress interactive screens asking for pwd of root
echo "mysql-server mysql-server/root_password select $MYSQL_ROOT_PWD" | debconf-set-selections
echo "mysql-server mysql-server/root_password_again select $MYSQL_ROOT_PWD" | debconf-set-selections
apt-get install -y mysql-server
apt-get install --yes --force-yes -q xfsprogs
netstat -na | grep 3306 > /dev/null && echo 'mysql is running on 3306' || die "MySQL does not appear to be running on port 3306."
cat <<EOL > demisauce.sql
create database if not exists demisauce DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;
use mysql;
delete from user where user = '';
GRANT ALL PRIVILEGES ON demisauce.* TO 'ds_web'@'localhost' IDENTIFIED BY '$DEMISAUCE_MYSQL_PWD' WITH GRANT OPTION;
grant select, insert, update, create, drop, reload, shutdown, alter, super, lock tables, replication client on *.* to 'backup-user'@'localhost' identified by '$DEMISAUCE_MYSQL_PWD'; 
flush privileges;
EOL
mysql -uroot -p$MYSQL_ROOT_PWD < demisauce.sql || die "Could not set up database for Demisauce."
rm -f demisauce.sql

/etc/init.d/mysql stop
killall mysqld_safe

if [ "$VMOREC2" = 'ec2' ] ; then
    echo " It appears to be EC2, creating xfs fs"
    mkfs.xfs /dev/sdh
    echo "/dev/sdh /vol xfs noatime 0 0" >> /etc/fstab
    mkdir /vol
    mount /vol
else
    # vm
    mkdir /vol
fi
mkdir /vol/lib /vol/log /vol/tmp
#sudo chown -R mysql:mysql
chown -R mysql:mysql /vol/lib
chown -R mysql:mysql /vol/log
chown -R mysql:mysql /vol/tmp


mv /var/lib/mysql /vol/lib/
mv /var/log/mysql /vol/log/
test -f /vol/log/mysql/mysql-bin.index &&
  perl -pi -e 's%/var/log/%/vol/log/%' /vol/log/mysql/mysql-bin.index

escaped_mysql_home="\/vol\/lib"
echo "New escaped_mysql_home = $escaped_mysql_home"
#  http://ubuntuforums.org/showthread.php?t=831147
# update apparmor 
#  /vol/tmp/ rw,
#  /vol/tmp/* rw,
#  /var/log/mysql.log rw,
#  /var/log/mysql.err rw,
#  /vol/lib/mysql/ r,
#  /vol/lib/mysql/** rwk,
#  /vol/log/mysql/ r,
#  /vol/log/mysql/* rw,
#  /var/run/mysqld/mysqld.pid w,
#  /var/run/mysqld/mysqld.sock w,
echo "---- /etc/apparmor.d/usr.sbin.mysqld  "
perl -pi -e "s/\/var\/lib\/mysql\//\/vol\/lib\/mysql\//g" /etc/apparmor.d/usr.sbin.mysqld || die "could not change apparmor.d/usr.sbin.mysqld"
perl -pi -e "s/\/var\/log\/mysql\//\/vol\/log\/mysql\//g" /etc/apparmor.d/usr.sbin.mysqld || die "could not change apparmor.d/usr.sbin.mysqld"
perl -pi -e "s/network tcp,/network tcp,\n\n  \/vol\/tmp\/ rw,\n  \/vol\/tmp\/* rw,/g" /etc/apparmor.d/usr.sbin.mysqld || die "problems with apparmor.d/usr.sbin.mysqld"


/vol/tmp/ rw,
/vol/tmp/* rw,
echo "---- making changes to /etc/mysql/my.cnf  "
# update datadir=/vol/lib/mysql and tmpdir=/vol/tmp/
perl -pi -e "s/\/var\/lib\/mysql/$escaped_mysql_home/g" /etc/mysql/my.cnf || die "could not change my.cnf"
perl -pi -e "s/\/tmp/\/vol\/tmp/g" /etc/mysql/my.cnf || die "could not change my.cnf"
perl -pi -e "s/skip\-external\-locking/skip\-external\-locking\nlog\-bin/g" /etc/mysql/my.cnf || die "could not change my.cnf"
cat > /etc/mysql/conf.d/mysql-ec2.cnf <<EOM
[mysqld]
innodb_file_per_table
datadir          = /vol/lib/mysql
log_bin          = /vol/log/mysql/mysql-bin.log
max_binlog_size  = 1000M
#log_slow_queries = /vol/log/mysql/mysql-slow.log
#long_query_time  = 10
EOM
rsync -aR /etc/mysql /vol/

/etc/init.d/apparmor restart
/etc/init.d/mysql restart


 