#!/usr/bin/env bash
#  A script to Install Demisauce Python Web Application
#       Depends on python, mysql-client, git  (see install.sh)
#       should work on *nix (mac/linux)
# 
# Command line options:
#
#   -d NAME                 - Directory to install into:  defaults to /home/demisauce
#   -p PWD                  - Password for MySQL:  Defaults to a demisauce
#   -r ROLE                 - Role (prod|dev) should it set up con jobs etc? default=prod
#
# Examples:
#
#   Build Demisauce on your machine
#
#   $./install_demisauce install    \
#   -d    /home/demisauce           \
#   -p   $ecr3t
# 
#   Upgrade Demisauce from source
#
#   $./install_demisauce upgrade
#
#----------------------------------------------------
function die
{
    echo $*
    exit 1
}
# Get all arguments if not supplied
function askArgs
{
    echo -en "Please enter 'install' or 'upgrade' \
    return to accept:   install"
    read installorupgrade
    if [ "$installorupgrade" != "" ] ; then
        UPGRADE_OR_INSTALL=$installorupgrade
    fi
    echo -en "Please enter password for the MySQL password for the demisauce web app or \
    return to accept [demisauce]"
    read pwd
    if [ "$pwd" != "" ] ; then
        DEMISAUCE_MYSQL_PWD=$pwd
    fi
    echo -en "Please enter home directory to install into: or \
    return to accept:   /home/demisauce/ds:   "
    read home
    if [ "$home" != "" ] ; then
        DEMISAUCE_HOME=$home
    fi
    echo -en "Please enter 'prod' or 'dev', for just base or include cron jobs: or \
    return to accept:  'prod'   :   "
    read role
    if [ "$role" != "" ] ; then
        INSTALL_ROLE=$role
    fi
    echo -en "Please enter 'ec2' or 'vm' \
    return to accept:  'ec2'   :   "
    read vmorec2
    if [ "$vmorec2" != "" ] ; then
        VMOREC2=$vmorec2
    fi
}

#----------  Start of program
UPGRADE_OR_INSTALL='install'
DEMISAUCE_HOME="/home/demisauce/ds"
DEMISAUCE_MYSQL_PWD="demisauce"
INSTALL_ROLE="prod"
VMOREC2="ec2"

# IP="$(wget -o/dev/null -O- http://jackson.io/ip/)"
# http://jackson.io/ip/service.html
#TODO: this doesn't work on mac
#linux$  eth0   inet addr:192.168.0.106  Bcast:192.168.0.255  Mask:255.255.255.0
#mac$ en0   inet 192.168.0.101 netmask 0xffffff00 broadcast 192.168.0.255
HOSTNAME=`ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}'`

if [ $# -eq "0" ] ; then
    askArgs
else 
    UPGRADE_OR_INSTALL=$1 
    shift 1
    if [ "$UPGRADE_OR_INSTALL" = "install" ] || [ "$UPGRADE_OR_INSTALL" = "upgrade" ] ; then
        while [ $# -gt 0 ]; do
            case $1 in
                -d) DEMISAUCE_HOME=$2;                              shift 2 ;;
                -p) DEMISAUCE_MYSQL_PWD=$2;                         shift 2 ;;
                -r) INSTALL_ROLE=$2;                                shift 2 ;;
                -e) VMOREC2=$2;                                     shift 2 ;;
                *)             echo "$0: Unrecognized option: $2" >&2; exit 1;
            esac
        done
    else
        echo 'first argument must be install or upgrade' ; die
    fi
fi

DEMISAUCE_WEB_HOME="$DEMISAUCE_HOME/current_web"
echo "DEMISAUCE_HOME = $DEMISAUCE_HOME; DEMISAUCE_MYSQL_PWD = $DEMISAUCE_MYSQL_PWD \
    install or upgrade? = $UPGRADE_OR_INSTALL"
echo "Demisauce web Home:   $DEMISAUCE_WEB_HOME"

#  each new version stored in different named version, then point to current
#  like:    /demisauce/ds/2008122811   (yyyymmddhh)
VERSION_FOLDER=$(date +"%y%m%d%H")
mkdir -p $DEMISAUCE_HOME
mkdir -p "$DEMISAUCE_HOME/log"  # make log directory
# reassign home to versioned folder
DEMISAUCE_VERSION_HOME=$DEMISAUCE_HOME/$VERSION_FOLDER
echo "New Home:  $DEMISAUCE_VERSION_HOME"
mkdir -p $DEMISAUCE_VERSION_HOME # new one w version
cd $DEMISAUCE_VERSION_HOME

echo "---- Downloading Demisauce SRC from github ------------"
git clone -q git://github.com/araddon/demisauce.git
#Create /home/demisauce/current_web pointing to /home/demisauce/ds/2008122812/demisauce/demisauce/trunk
ln -s $DEMISAUCE_VERSION_HOME/demisauce/demisauce/trunk $DEMISAUCE_WEB_HOME



echo '---- installing DemisaucePY ---------'
cd "$DEMISAUCE_VERSION_HOME/demisauce/demisaucepy/trunk/"
python setup.py install

cd "$DEMISAUCE_VERSION_HOME/demisauce/demisauce/trunk"

# can't i get rid of this?  why is it needed?
python setup.py install  # is this bad, at least it doesn't move items to path?
echo " calling pwd next"
pwd
echo "------  setting up production.ini    -----------"
paster make-config demisauce production.ini
# replace console logging with file:   logfile = console
escaped_demisauce_home="${DEMISAUCE_HOME//\//\/}"
echo "escaped demisauce home  $escaped_demisauce_home"
perl -pi -e "s/logfile\ =\ console/logfile\ =\ $escaped_demisauce_home\/log\/paster.log/g" production.ini || echo "Could not change logging "
# replace sqllite with mysql and change pwd
perl -pi -e "s/sqlalchemy.default.url\ =\ sqlite/\#sqlalchemy.default.url\ =\ sqlite/g" production.ini || echo "Could not comment out sqllite"
perl -pi -e "s/\#sqlalchemy.default.url\ =\ mysql/\sqlalchemy.default.url\ =\ mysql/g" production.ini || echo "Could not un-comment mysql"
perl -pi -e "s/ds_web:password/ds_web:$DEMISAUCE_MYSQL_PWD/g" production.ini || echo "Could not change mysql pwd"
perl -pi -e "s/http:\/\/localhost:4950/http:\/\/$HOSTNAME/g" production.ini || echo "Failed attempting to update Hostname"

HOSTNAME2="http://$HOSTNAME"
if [ $INSTALL_ROLE = "prod" ] ; then
    echo "Now calling paster setup-app production.ini"
    paster setup-app production.ini
    
    paster updatesite -s $HOSTNAME2 -i production.ini
    echo "-----  create init.d startup scripts for demisauce   
    available at /etc/init.d/demisauce_web (start|stop|restart) ------------"
    rm -f /etc/init.d/demisauce_web
    mv $DEMISAUCE_VERSION_HOME/demisauce/install/install_initd.sh /etc/init.d/demisauce_web
    chmod +x /etc/init.d/demisauce_web
    #/etc/init.d/install_initd.sh "$DEMISAUCE_HOME/demisauce/demisauce/trunk"
    /etc/init.d/demisauce_web start
    #paster serve --daemon production.ini
    echo "-----  Creating cron job to restart paster if it fails -----------"
    cat <<EOL > /var/spool/cron/crontabs/root.tmp
     */2 * * * * /etc/init.d/demisauce_web start
EOL
    crontab /var/spool/cron/crontabs/root.tmp
elif [ $INSTALL_ROLE = "dev" ] ; then
    paster setup-app devmysql.ini
    paster updatesite -s $HOSTNAME2 -i devmysql.ini
fi


echo "---------------------"
echo "--- Your server is available at:   $HOSTNAME"
