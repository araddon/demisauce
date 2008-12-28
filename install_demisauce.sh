#!/usr/bin/env bash
#  install_demisauce.sh demisauce_home_dir demisaucedb_pwd

#----------  Start of program
ARGS=2
if [ $# -ne "$ARGS" ]
then
    echo "Usage: install_demisauce.sh demisauce_dir  demisauce_db_pwd_for_web  all"
    die 
else
    DEMISAUCE_HOME=$1
    DEMISAUCE_MYSQL_PWD=$2
fi

function die
{
    echo $*
    exit 1
}

#TODO add version/date to this like capistrano:   
mkdir -p $DEMISAUCE_HOME
mkdir -p "$DEMISAUCE_HOME/log"  # make log directory
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

echo "-----  create init.d startup scripts for demisauce available at /etc/init.d/demisauce_web (start|stop|restart) ------------"
mv $DEMISAUCE_HOME/install_initd.sh /etc/init.d/demisauce_web
chmod +x /etc/init.d/demisauce_web
/etc/init.d/install_initd.sh "$DEMISAUCE_HOME/demisauce/demisauce/trunk"
/etc/init.d/demisauce_web start
#paster serve --daemon production.ini
echo "-----  Creating cron job to restart paster if it fails -----------"
cat <<EOL > /var/spool/cron/crontabs/root.tmp
 */2 * * * * /etc/init.d/demisauce_web start
EOL
crontab /var/spool/cron/crontabs/root.tmp


