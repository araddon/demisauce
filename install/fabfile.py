"""
    see documentaiton:  http://github.com/araddon/demisauce/tree/master/install
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
    env.type = 'vm'
    env.environment = 'dev'

def vm106():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.106']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu9.04'
    env.type = 'vm'
    env.environment = 'dev'

def vm107():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.107']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu9.04'
    env.type = 'vm'
    env.environment = 'dev'

def ec2prod():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.107']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.type = 'ec2'
    env.os = 'ubuntu9.04'
    env.environment = 'prod'


#   Tasks   =======================
def release(userdbpwd):
    'Deploy a new/updated release to the target environment'
    _nginx_release()
    _demisauce_deploy_code(userdbpwd)
    sudo("/etc/init.d/nginx restart")

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

def _mysql(rootmysqlpwd,mysqlpwd):
    put('%(local_path)s/install/install_mysql.sh' % env, '/tmp/install_mysql.sh' % env)
    sudo('chmod +x /tmp/install_mysql.sh; /tmp/install_mysql.sh %s %s %s' % (rootmysqlpwd,mysqlpwd,env.type))
    sudo('rm /tmp/install_mysql.sh')

def _zamanda(mysqlpwd):
    """ install backup tools"""
    """setting myhostname: demisauce
    [192.168.0.107] out: setting alias maps
    [192.168.0.107] out: setting alias database
    [192.168.0.107] out: mailname is not a fully qualified domain name.  Not changing /etc/mailname.
    [192.168.0.107] out: setting destinations: /etc/mailname, demisauce, localhost.localdomain, localhost
    [192.168.0.107] out: setting relayhost: 
    [192.168.0.107] out: setting mynetworks: 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
    [192.168.0.107] out: setting mailbox_size_limit: 0
    [192.168.0.107] out: setting recipient_delimiter: +
    [192.168.0.107] out: setting inet_interfaces: all
    
    """
    put('%(local_path)s/install/install_zamanda.sh' % env, '/tmp/install_zamanda.sh' % env)
    sudo('chmod +x /tmp/install_zamanda.sh; /tmp/install_zamanda.sh %s %s %s' % (mysqlpwd,mysqlpwd,env.type))
    sudo('rm /tmp/install_zamanda.sh')

def _nginx():
    """Installs Nginx"""
    sudo("""echo "deb http://ppa.launchpad.net/jdub/devel/ubuntu hardy main" >> /etc/apt/sources.list
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E9EEF4A1""")
    sudo("apt-get -y update; apt-get -y install nginx")
    get('/etc/nginx/mime.types', '%s/nginx/mime.types' % INSTALL_ROOT)
    get('/etc/nginx/nginx.conf', '%s/nginx/nginx.conf' % INSTALL_ROOT)
    sudo("mkdir -p /vol/log/nginx")

def _nginx_release():
    sudo("/etc/init.d/nginx stop")
    with cd("/etc/nginx"):
        sudo("rm nginx.conf")
        sudo("rm sites-enabled/demisauce;")
    put('%s/nginx/nginx.conf' % INSTALL_ROOT, '/tmp/nginx.conf')
    put('%s/nginx/sites-enabled/demisauce' % INSTALL_ROOT, '/tmp/sa-ds')
    sudo('mv /tmp/nginx.conf /etc/nginx/nginx.conf')
    sudo('mv /tmp/sa-ds /etc/nginx/sites-enabled/demisauce')


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

def _demisauce_pre_reqs():
    """Install the python modules necessary"""
    sudo('apt-get -y install python-mysqldb')
    sudo('easy_install http://gdata-python-client.googlecode.com/files/gdata.py-1.1.1.tar.gz')

def _demisauce_deploy_code(dsmysqlpwd):
    put('%(local_path)s/install/install_demisauce.sh' % env, '/tmp/install_demisauce.sh' % env)
    sudo('chmod +x /tmp/install_demisauce.sh; /tmp/install_demisauce.sh install -d %s -p %s -r %s -e %s' % \
            ("/home/demisauce/ds",dsmysqlpwd,env.environment,env.type))
    sudo('rm /tmp/install_demisauce.sh')

def ec2_save_image():
    """Takes an instance on EC2 and saves to S3"""
    raise NotImplemented("needs to be done")

def build_all(rootmysqlpwd="demisauce",userdbpwd="demisauce"):
    require('hosts', provided_by=[vm107,vm106,ec2prod])
    #_linux_base()
    #_gearman() # includes memcached
    #_memcached()
    #_mysql(rootmysqlpwd,dbpwd)
    #_zamanda(dbpwd)
    #_nginx()
    _demisauce_pre_reqs()
    release(userdbpwd)

