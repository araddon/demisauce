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
    echo -en "Please enter server role (web|db|phpweb|memcache|all): or
return to accept [all]"
    read SERVER_ROLE
    if [ "$SERVER_ROLE" = "" ] ; then
        SERVER_ROLE="all"
    fi
    echo -en "Please enter 'ec2' or 'vm' 
    return to accept:  'ec2'   :   "
    read vmorec2
    if [ "$vmorec2" != "" ] ; then
        VMOREC2=$vmorec2
    fi
}

#-----------------------------------  Start of program
DEMISAUCE_HOME='/home/demisauce'
MYSQL_HOME='/vol/lib'
ZRM_HOME='/vol/mysql-zrm'
DEMISAUCE_WEB_HOME=$DEMISAUCE_HOME/current_web
VMOREC2="ec2"
SERVER_ROLE='all'

checkRoot
askArgs

cd /tmp
# Upgrade/install packages
apt-get -y update
# some basics
apt-get install --yes --force-yes -q wget unzip cron rsync

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "db" ] 
then
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
    mkdir /vol/lib /vol/log
    chown mysql:mysql /vol/lib
    chown mysql:mysql /vol/log
    mv /var/lib/mysql /vol/lib/
    mv /var/log/mysql /vol/log/
    test -f /vol/log/mysql/mysql-bin.index &&
      perl -pi -e 's%/var/log/%/vol/log/%' /vol/log/mysql/mysql-bin.index
    #chown mysql:mysql "$MYSQL_HOME/tmp"
    escaped_mysql_home="\/vol\/lib"
    echo "New escaped_mysql_home = $escaped_mysql_home"
    #rmdir /var/lib/mysql
    # update datadir=/mnt/mysql and tmpdir=/mnt/mysql/tmp/
    echo "---- making changes to /etc/mysql/my.cnf  "
    #perl -pi -e "s/\/var\/lib\/mysql/$escaped_mysql_home/g" /etc/mysql/my.cnf || die "could not change my.cnf"
    #perl -pi -e "s/\/tmp/$escaped_mysql_home\/tmp/g" /etc/mysql/my.cnf || die "could not change my.cnf"
    #perl -pi -e "s/skip\-external\-locking/skip\-external\-locking\nlog\-bin/g" /etc/mysql/my.cnf || die "could not change my.cnf"
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
    
    # install zamanda backup , zamanda depends on mailx
    echo "----  Installing Zamanda Backup for MySql, needs mailx for sending emails"
    apt-get --yes --force-yes -q install mailx libxml-parser-perl libdbd-mysql-perl
    # if no mail transport agent defined mailx dependency will get one here
    apt-get -f install 
    cd /tmp
    wget http://www.zmanda.com/downloads/community/ZRM-MySQL/2.1/Debian/mysql-zrm_2.1_all.deb
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
fi

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "web" ] 
then
    echo "----  installing git-core ------------"
    apt-get install --yes --force-yes -q git-core  # needed to get recent build from git
    echo "----  installing apache  -------------"
    apt-get install --yes --force-yes -q apache2 
    apt-get install --yes --force-yes -q libapache2-mod-fcgid  #  What is this for again?
    # http://wiki.pylonshq.com/display/pylonscookbook/Apache+as+a+reverse+proxy+for+Pylons
    # http://serbiancafe.wordpress.com/2006/10/20/apaches-proxypass-on-ubuntu/
    a2enmod proxy
    a2enmod proxy_http
    a2enmod rewrite
    echo "modifying /etc/apache2/mods-available/proxy.conf to allow proxy from local"
    #comment out deny all, and enable from localhost
    perl -pi -e s/Deny\ from\ all/\#Deny\ from\ all/g /etc/apache2/mods-available/proxy.conf || die "Could not comment out Deny All"
    perl -pi -e s/\#Allow\ from\ \.example\.com/Allow\ from\ localhost/g /etc/apache2/mods-available/proxy.conf || die "failed to allow localhost proxy"
    
    echo "----- Creating new /etc/apache2/sites-available/default  file  ------------"
    mv /etc/apache2/sites-available/default /etc/apache2/sites-available/default.bak
    PASTER_HOST=http://127.0.0.1:4950/\$1
    cat <<EOL > /etc/apache2/sites-available/default
<VirtualHost *>
        ServerAdmin webmaster@localhost
        DocumentRoot $DEMISAUCE_WEB_HOME/demisauce/public/
        
        Alias /blog /home/demisauce/wordpress
        <Directory "/home/demisauce/wordpress">
            AllowOverride All
            Order allow,deny
            Allow from all
        </Directory>
        
        RewriteEngine On
        #RewriteLog /home/demisauce/log/apacherw.txt
        #RewriteLogLevel 3
        #RewriteCond %{DOCUMENT_ROOT}%{REQUEST_FILENAME} -f
        RewriteCond %{REQUEST_FILENAME} !\.(php|js|css|gif|jpg|png|ico|txt|swf|mp3|pdf|ps|wav|mid|midi|flv|zip|rar|gz|tar|bmp)$ [NC]
        RewriteCond %{REQUEST_URI} !^/blog(.*)$ [NC]
        RewriteRule ^/(.*) $PASTER_HOST [P]
        
        <Directory />
                Options FollowSymLinks
                allow from all
                AllowOverride None
        </Directory>
        
        ErrorLog /var/log/apache2/error.log
        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel info
        CustomLog /var/log/apache2/access.log combined
        ServerSignature On
</VirtualHost>
EOL
fi

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "memcache" ] 
then
    echo "----  installing memcached ------------"
    apt-get install --yes --force-yes -q memcached
    echo "SECURITY NOTICE:  Enabling memcached from remote"
    #comment out line for -l 127.0.0.1 which restricts to only local machine
    perl -pi -e s/-l\ 127.0.0.1/\#-l\ 127.0.0.1/g /etc/memcached.conf || die "Could not comment out local only memcached"
fi

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "wordpress" ] 
then
    echo "----  installing php ------------"
    apt-get install --yes --force-yes -q php5 php5-dev libapache2-mod-php5 php5-mysql php5-memcache 
    echo "----  adding memcached extension to php  /etc/php5/apache2/php.ini "
    #  Adds this:    extension=memcache.so    
    perl -pi -e s/\;\ extension_dir\ directive\ above./\;\ extension_dir\ directive\ above.\\nextension=memcache.so/g /etc/php5/apache2/php.ini || die "Could not update php.ini"
fi

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "web" ] || [ $SERVER_ROLE = "wordpress" ] 
then
    /etc/init.d/apache2 restart
fi

# install the demisauce python web app
cd /tmp
wget http://github.com/araddon/demisauce/raw/master/install/install_demisauce.sh
chmod +x install_demisauce.sh
./install_demisauce.sh install -d $DEMISAUCE_HOME -p $DEMISAUCE_MYSQL_PWD -r prod -e $VMOREC2

#./install_wordpress.sh
