# http://lethain.com/entry/2008/nov/04/deploying-django-with-fabric/
# http://wp.uberdose.com/2006/10/16/ssh-automatic-login/
# http://stii.co.za/python/upgrade-wordpress-using-python-fabric/
# http://en.wikipedia.org/wiki/Secure_copy
"""
$ fab vm build -p 
"""
from __future__ import with_statement # needed for python 2.5
from fabric.api import *
import os, simplejson
from optparse import OptionParser
#import fab_recipes

# globals
env.project_name = 'demisauce'
INSTALL_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.realpath(INSTALL_ROOT + '/../' )
env.path = "/home/demisauce"
env.local_path = PROJECT_ROOT
env.redis_version = "redis-1.02"

# environments  ========================
def imac():
    "Dev imac machine"
    env.hosts = ['localhost']
    env.user = 'aaron'
    env.path = env.local_path

def vm101():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.101']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu8.04'

def vm106():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.106']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu9.04'

def vm107():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.107']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu9.04'

def ec2prod():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.107']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu9.04'


#   Tasks   =======================
def deploy():
    'Deploy the app to the target environment'
    local("python setup.py sdist")
    put("bin/bundle.zip", "bundle.zip")
    sudo("./install.sh bundle.zip")

def _initial_setup():
    """sets up new server by doing installs, folder creations etc"""
    sudo("rm -f install.sh")
    put("install.sh", "install.sh")
    sudo("chmod +x install.sh" )
    sudo("./install.sh %s" % (config.mysql_pwd))

def _memcached():
    sudo("apt-get install --yes --force-yes -q memcached")
    print("SECURITY NOTICE:  Enabling memcached from remote")
    #comment out line for -l 127.0.0.1 which restricts to only local machine
    sudo('perl -pi -e s/-l\ 127.0.0.1/\#-l\ 127.0.0.1/g /etc/memcached.conf')

def _mysql(mysqlpwd,vm_or_ec2):
    put('%(local_path)s/install/install_mysql.sh' % env, '/tmp/install_mysql.sh' % env)
    sudo('chmod +x /tmp/install_mysql.sh; /tmp/install_mysql.sh %s %s %s' % (mysqlpwd,mysqlpwd,vm_or_ec2))
    sudo('rm /tmp/install_mysql.sh')

def _zamanda(mysqlpwd,vm_or_ec2):
    put('%(local_path)s/install/install_zamanda.sh' % env, '/tmp/install_zamanda.sh' % env)
    sudo('chmod +x /tmp/install_zamanda.sh; /tmp/install_zamanda.sh %s %s %s' % (mysqlpwd,mysqlpwd,vm_or_ec2))
    sudo('rm /tmp/install_zamanda.sh')

def _gearman():
    """Install Gearman, requires base linux"""
    sudo("cp /etc/apt/sources.list /etc/apt/sources.list.orig")
    if env.os == 'ubuntu8.04':
        sudo("""echo "deb http://ppa.launchpad.net/drizzle-developers/ppa/ubuntu hardy main
deb-src http://ppa.launchpad.net/drizzle-developers/ppa/ubuntu hardy main" >> /etc/apt/sources.list""")
    elif env.os == "ubuntu9.04":
        sudo("""echo "deb http://ppa.launchpad.net/drizzle-developers/ppa/ubuntu jaunty main
deb-src http://ppa.launchpad.net/drizzle-developers/ppa/ubuntu jaunty main" >> /etc/apt/sources.list""")
    elif env.os == "ubuntu9.10":
        sudo("""echo "deb http://ppa.launchpad.net/drizzle-developers/ppa/ubuntu karmic main
deb-src http://ppa.launchpad.net/drizzle-developers/ppa/ubuntu karmic main" >> /etc/apt/sources.list""")
    
    sudo("apt-get update; apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 06899068")
    sudo("apt-get update; apt-get install -y gearman gearman-job-server gearman-tools libgearman2 libgearman-dev libgearman-dbg libgearman-doc")

def _gearmanDrizzle():
    """Install Gearman, requires base linux"""
    sudo("cp /etc/apt/sources.list /etc/apt/sources.list.orig")
    if env.os == 'ubuntu8.04':
        sudo("""echo "deb http://ppa.launchpad.net/gearman-developers/ppa/ubuntu hardy main
deb-src http://ppa.launchpad.net/gearman-developers/ppa/ubuntu hardy main" >> /etc/apt/sources.list""")
    elif env.os == "ubuntu9.04":
        sudo("""echo "deb http://ppa.launchpad.net/gearman-developers/ppa/ubuntu jaunty main
deb-src http://ppa.launchpad.net/gearman-developers/ppa/ubuntu jaunty main" >> /etc/apt/sources.list""")
    elif env.os == "ubuntu9.10":
        sudo("""echo "deb http://ppa.launchpad.net/gearman-developers/ppa/ubuntu karmic main
deb-src http://ppa.launchpad.net/gearman-developers/ppa/ubuntu karmic main" >> /etc/apt/sources.list""")
    
    sudo("apt-get update; apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1C73E014")
    sudo("apt-get update; apt-get install -y gearman gearman-job-server gearman-tools libgearman2 libgearman-dev libgearman-dbg libgearman-doc")

def _linux_base():
    """Installs base Linux essentials (ubuntu install)"""
    """
    First you have installed base ubuntu and ssh, wget:
    sudo apt-get -y update; sudo apt-get -y install openssh-server wget
    """
    sudo("apt-get -y update; apt-get -y install wget unzip cron rsync python-setuptools")
    sudo("apt-get -y install build-essential git-core; apt-get -y update")

def _demisauce(dsmysqlpwd,vm_or_ec2):
    put('%(local_path)s/install/install_demisauce.sh' % env, '/tmp/install_demisauce.sh' % env)
    sudo('chmod +x /tmp/install_demisauce.sh; /tmp/install_demisauce.sh install -d %s -p %s -r prod -e %s' % ("/home/demisauce",dsmysqlpwd,vm_or_ec2))
    sudo('rm /tmp/install_demisauce.sh')
    #install.sh mysql_root_password  demisauce_mysql_pwd vm


def build_vm107(ospwd="",dbpwd=""):
    require('hosts', provided_by=[vm107])
    #_linux_base()
    #_gearman() # includes memcached
    #_memcached()
    _mysql(dbpwd,'vm')
    #_zamanda(dbpwd,'vm')
    #_demisauce(dbpwd,'vm')

def build_vm106(ospwd="",dbpwd=""):
    require('hosts', provided_by=[vm106])
    #_linux_base()
    #_gearman() # includes memcached
    #_memcached()
    _mysql(dbpwd,'vm')
    #_zamanda(dbpwd,'vm')
    #_demisauce(dbpwd,'vm')

def build_vm101(ospwd="",dbpwd=""):
    require('hosts', provided_by=[vm101])
    #_linux_base()
    #_gearman()

def build_newec2prod(ospwd="",dbpwd=""):
    require('hosts', provided_by=[ec2prod])
    #_linux_base()
    #_gearman()
    #_mysql(dbpwd,'vm')
    #_zamanda(dbpwd,'vm')
    #_demisauce(dbpwd,'ec2')
