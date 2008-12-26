#!/usr/bin/env bash
#  install_demisauce.sh demisauce_home_dirdemisaucedb_pwd
function die
{
    echo $*
    exit 1
}
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


#TODO add version/date to this get
mkdir -p $DEMISAUCE_HOME
mkdir -p "$DEMISAUCE_HOME/log"  # make log directory
cd $DEMISAUCE_HOME
echo "\n---- Downloading Demisauce SRC from github ------------"
git clone -q git://github.com/araddon/demisauce.git


cd /tmp
echo "--- installing python-mysql -------------"
apt-get install --yes --force-yes -q python-mysqldb
wget http://peak.telecommunity.com/dist/ez_setup.py
python ez_setup.py
rm -f ez_setup.py

easy_install -U flup # part of proxy server
easy_install sqlalchemy==0.4.8
easy_install pylons==0.9.6.2
easy_install tempita
#easy_install Genshi==0.5.1
easy_install webhelpers==0.6
http://code.google.com/p/gdata-python-client/
wget http://gdata-python-client.googlecode.com/files/gdata.py-1.2.3.tar.gz
tar -xzvf gdata.py-1.2.3.tar.gz 
rm gdata*.tar.gz
cd gdata.py-1.2.3
python setup.py install
cd ..
rm -rf gdata.py-1.2.3

cd "$DEMISAUCE_HOME/demisauce/demisaucepy/trunk/"
python setup.py install

cd "$DEMISAUCE_HOME/demisauce/demisauce/trunk"
python setup.py install  # can't i get rid of this?  why is it needed?
echo "------  setting up production.ini    -----------\n------------------------------"
paster make-config demisauce production.ini
paster setup-app production.ini

# replace console logging with file:   logfile = console
perl -pi -e "s/logfile\ =\ console/logfile\ =\/home\/demisauce\/log\/paster.log/g" production.ini || echo "Could not change logging "
# replace sqllite with mysql and change pwd
perl -pi -e "s/sqlalchemy.default.url\ =\ sqlite/\#sqlalchemy.default.url\ =\ sqlite/g" production.ini || echo "Could not comment out sqllite"
perl -pi -e "s/\#sqlalchemy.default.url\ =\ mysql/\sqlalchemy.default.url\ =\ mysql/g" production.ini || echo "Could not un-comment mysql"
perl -pi -e "s/ds_web:password/ds_web:$DEMISAUCE_MYSQL_PWD/g" production.ini || echo "Could not change mysql pwd"

paster serve --daemon production.ini

