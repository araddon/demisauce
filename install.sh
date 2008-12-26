#!/usr/bin/env bash
# chmod +x install.sh
#  install.sh mysql_password  demisaucedb_pwd all
#
# http://developer.amazonwebservices.com/connect/entry.jspa?externalID=1085
# http://docs.amazonwebservices.com/AWSEC2/2008-02-01/DeveloperGuide/index.html?CLTRG-run-instances.html
DEMISAUCE_HOME='/home/demisauce'
function die
{
    echo $*
    exit 1
}
# Get all arguments if not supplied
function askArgs
{
    echo "Please enter your MySQL root password:"
    read MYSQL_ROOT_PWD
    echo "Please enter password for the MySQL password for the demisauce web app"
    read DEMISAUCE_MYSQL_PWD
    echo "Please enter 'web', 'db', 'phpweb', 'memcache', or 'all' Role for server"
    read SERVER_ROLE
}

#-----------------------------------  Start of program
ARGS=3
if [ $# -ne "$ARGS" ]
then
    if [ $# -ne "0" ]
    then
        echo "Usage: install.sh mysql_password  demisauce_db_pwd all"
        echo "You can also just run ./install.sh to have the script guide you through the setup process."
        die 
    else
        askArgs
    fi
else
    MYSQL_ROOT_PWD=$1
    DEMISAUCE_MYSQL_PWD=$2
    SERVER_ROLE=$3
fi

cd /tmp
# Upgrade/install packages
sudo apt-get -y update
# some basics
apt-get install --yes --force-yes -q wget unzip

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "db" ] 
then
    echo "----   Starting MySQL install  ------------"
    echo "mysql-server mysql-server/root_password select $MYSQL_ROOT_PWD" | debconf-set-selections
    echo "mysql-server mysql-server/root_password_again select $MYSQL_ROOT_PWD" | debconf-set-selections
    apt-get install -y mysql-server
    netstat -na | grep 3306 > /dev/null && echo 'mysql is running on 3306' || die "MySQL does not appear to be running on port 3306."
    cat <<EOL > demisauce.sql
    create database if not exists demisauce character set utf8;
    delete from user where user = '';
    GRANT ALL PRIVILEGES ON demisauce.* TO 'ds_web'@'localhost' IDENTIFIED BY '$DEMISAUCE_MYSQL_PWD' WITH GRANT OPTION;
    flush privileges;
EOL
    mysql -uroot -p$MYSQL_ROOT_PWD < demisauce.sql || die "Could not set up database for Demisauce.  Is your root password correct?"
    rm -f demisauce.sql
    # mysql -u root -p$MYSQL_ROOT_PWD -Bse "use mysql; delete from user where user = '';"
    # mysql -u root -p$MYSQL_ROOT_PWD -Bse "create database demisauce;GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP ON demisauce.* TO 'ds_web'@'%' IDENTIFIED BY '$DEMISAUCE_MYSQL_PWD';"
fi

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "web" ] 
then
    echo "----  installing git-core ------------"
    apt-get install --yes --force-yes -q git-core # needed to get recent build from git
    echo "----  installing apache  -------------"
    apt-get install --yes --force-yes -q apache2 
    apt-get install --yes --force-yes -q libapache2-mod-fcgid  #  What is this for again?
    # http://wiki.pylonshq.com/display/pylonscookbook/Apache+as+a+reverse+proxy+for+Pylons
    # http://serbiancafe.wordpress.com/2006/10/20/apaches-proxypass-on-ubuntu/
    sudo a2enmod proxy
    sudo a2enmod proxy_http
    cat <<EOL > /etc/apache2/httpd.conf
    <VirtualHost *>
        #ServerName demisauce.dev
        #ServerAlias demisauce.dev

        # Logfiles  (folders must exist)
        #ErrorLog  /home/demisauce/log/error.log
        #CustomLog /home/demisauce/log/access.log combined

        # Proxy
        ProxyPass / http://localhost:4950/ retry=5
        ProxyPassReverse / http://localhost:4950/
        ProxyPreserveHost On
        <Proxy *>
            Order deny,allow
            Allow from all
        </Proxy>
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
#./install_demisauce.sh $DEMISAUCE_HOME $DEMISAUCE_MYSQL_PWD


#./install_wordpress.sh



