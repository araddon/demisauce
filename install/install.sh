#!/usr/bin/env bash
# 
#  chmod +x install.sh
#  usage:   $install.sh mysql_root_password  demisauce_mysql_pwd role(all|web|db|memcached)
#
#  Starting from this base:   
#       apt-get update
#       apt-get install openssh-server wget
#  If VMWare:
#       apt-get install build-essential linux-headers-generic 
#       # Install VMware tools: 
#           http://samj.net/2008/06/installing-vmware-tools-in-ubuntu-804.html
# ----------------------------------------------------------------------------
#  TODO
#   - consider changing log level in apache2/sites-available/default
#   - other than ubuntu?
# ----------------------------------------------------------------------------
function die
{
    echo $*
    exit 1
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
}

#-----------------------------------  Start of program
DEMISAUCE_HOME='/home/demisauce'
DEMISAUCE_WEB_HOME=$DEMISAUCE_HOME/current_web
ARGS=3
if [ $# -ne "$ARGS" ]
then
    if [ $# -ne "0" ] ; then
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
apt-get install --yes --force-yes -q wget unzip cron

if [ $SERVER_ROLE = "all" ] || [ $SERVER_ROLE = "db" ] 
then
    echo "----   Starting MySQL install  ------------"
    # suppress interactive screens asking for pwd of root
    echo "mysql-server mysql-server/root_password select $MYSQL_ROOT_PWD" | debconf-set-selections
    echo "mysql-server mysql-server/root_password_again select $MYSQL_ROOT_PWD" | debconf-set-selections
    apt-get install -y mysql-server
    netstat -na | grep 3306 > /dev/null && echo 'mysql is running on 3306' || die "MySQL does not appear to be running on port 3306."
    cat <<EOL > demisauce.sql
    create database if not exists demisauce character set utf8;
    use mysql;
    delete from user where user = '';
    GRANT ALL PRIVILEGES ON demisauce.* TO 'ds_web'@'localhost' IDENTIFIED BY '$DEMISAUCE_MYSQL_PWD' WITH GRANT OPTION;
    flush privileges;
EOL
    mysql -uroot -p$MYSQL_ROOT_PWD < demisauce.sql || die "Could not set up database for Demisauce."
    rm -f demisauce.sql
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
        
        RewriteEngine On
        #RewriteCond %{DOCUMENT_ROOT}%{REQUEST_FILENAME} -f
        RewriteCond %{REQUEST_FILENAME} !\.(js|css|gif|jpg|png|ico|txt|swf|mp3|pdf|ps|wav|mid|midi|flv|zip|rar|gz|tar|bmp)$ [NC]
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
#./install_demisauce.sh install -d $DEMISAUCE_HOME -p $DEMISAUCE_MYSQL_PWD -r prod

#./install_wordpress.sh
