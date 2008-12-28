#!/usr/bin/env bash
#  A script to Install Demisauce Python Web Application
#       Depends on python, mysql-client, git  (see install.sh)
# 
# Command line options:
#
#    -d NAME                - Directory to install into:  defaults to /home/demisauce
#    -p PWD                 - Password for MySQL:  Defaults to a demisauce
#
# Examples:
#
#   Build Demisauce on your machine
#
#   $./install_demisauce install      \
#   -d    /home/demisauce               \
#   -p   mysecret
# 
#   Upgrade Demisauce from source
#
#   $./install_demisauce upgrade
#
#----------------------------------------------------

# Get all arguments if not supplied
function askArgs
{
    echo "Please home directory to install into"
    read DEMISAUCE_HOME
    echo "Please enter password for the MySQL password for the demisauce web app"
    read DEMISAUCE_MYSQL_PWD
}
#----------  Start of program
ARGS=2
if [ $1 == 'install']
then
    if [ $# -ne "$ARGS" ]
    then
        echo "Usage: install_demisauce.sh install_orupgrade(upgrade|install) -d demisauce_dir  -p demisauce_db_pwd_for_web "
        askArgs 
    else
        UPGRADE_OR_INSTALL = $1
        while [ $# -gt 0 ]; do
          case $2 in
            -d) DEMISAUCE_HOME=$3;                    shift 2 ;;
            -p) DEMISAUCE_MYSQL_PWD=$3;                         shift 2 ;;
            *)             echo "$0: Unrecognized option: $2" >&2; exit 1;
          esac
        done

        DEMISAUCE_HOME=$1
        DEMISAUCE_MYSQL_PWD=$2
    fi
fi

function die
{
    echo $*
    exit 1
}

die
mkdir -p $DEMISAUCE_HOME
mkdir -p "$DEMISAUCE_HOME/log"  # make log directory
#  each new version stored in different named version, then point to current
#  like:    /demisauce/2008122811   (yyyymmddhh)
VERSION_FOLDER=`python -c "from datetime import datetime as d; print d.now().strftime('%Y%m%d%H')"` 
# reassign home to versioned folder
DEMISAUCE_HOME=$DEMISAUCE_HOME/$VERSION_FOLDER
cd $DEMISAUCE_HOME
echo "\n---- Downloading Demisauce SRC from github ------------"
git clone -q git://github.com/araddon/demisauce.git


cd /tmp
echo "\n---- installing python-mysql -------------"
apt-get install --yes --force-yes -q python-mysqldb

echo "\n---- installing easy_install python instller ------------"
wget http://peak.telecommunity.com/dist/ez_setup.py
python ez_setup.py
rm -f ez_setup.py

easy_install -U flup # part of proxy server

echo '\n---- installing GData ---------'
easy_install http://gdata-python-client.googlecode.com/files/gdata.py-1.2.3.tar.gz

echo '\n---- installing DemisaucePY ---------'
cd "$DEMISAUCE_HOME/demisauce/demisaucepy/trunk/"
python setup.py install

cd "$DEMISAUCE_HOME/demisauce/demisauce/trunk"
# items i should be able to remove due to dependencies?
easy_install sqlalchemy==0.4.8
easy_install pylons==0.9.6.2
easy_install tempita
#easy_install Genshi==0.5.1   ?? dependencies?
easy_install webhelpers==0.6  # todo:  not needed after pylons .9.7
python setup.py install  # can't i get rid of this?  why is it needed?

echo "------  setting up production.ini    -----------\n"
paster make-config demisauce production.ini
# replace console logging with file:   logfile = console
perl -pi -e "s/logfile\ =\ console/logfile\ =\ $DEMISAUCE_HOME\/log\/paster.log/g" production.ini || echo "Could not change logging "
# replace sqllite with mysql and change pwd
perl -pi -e "s/sqlalchemy.default.url\ =\ sqlite/\#sqlalchemy.default.url\ =\ sqlite/g" production.ini || echo "Could not comment out sqllite"
perl -pi -e "s/\#sqlalchemy.default.url\ =\ mysql/\sqlalchemy.default.url\ =\ mysql/g" production.ini || echo "Could not un-comment mysql"
perl -pi -e "s/ds_web:password/ds_web:$DEMISAUCE_MYSQL_PWD/g" production.ini || echo "Could not change mysql pwd"

paster setup-app production.ini

echo "-----  create init.d startup scripts for demisauce   "
ech  " available at /etc/init.d/demisauce_web (start|stop|restart) \n------------"
#$ ln -s /home/simon/demo /home/jules/mylink3   #Create mylink3 pointing to demo

rm -f /etc/init.d/demisauce_web
mv $DEMISAUCE_HOME/install/install_initd.sh /etc/init.d/demisauce_web
chmod +x /etc/init.d/demisauce_web
/etc/init.d/install_initd.sh "$DEMISAUCE_HOME/demisauce/demisauce/trunk"
/etc/init.d/demisauce_web start
#paster serve --daemon production.ini
echo "-----  Creating cron job to restart paster if it fails -----------"
cat <<EOL > /var/spool/cron/crontabs/root.tmp
 */2 * * * * /etc/init.d/demisauce_web start
EOL
crontab /var/spool/cron/crontabs/root.tmp


