"""
    see documentaiton:  http://github.com/araddon/demisauce/tree/master/install
"""
from __future__ import with_statement # needed for python 2.5
from fabric.api import *
from fabric.contrib.project import rsync_project
import os, simplejson, datetime
#from optparse import OptionParser
#import fab_recipes

# TODO
#  - allow for remote networking on mysql  bind-address = 192.168.0.106 to allow from other servers in local
#  - 
# =============    globals
env.project_name = 'demisauce'
INSTALL_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.realpath(INSTALL_ROOT + '/../' )
env.path = "/home/demisauce"
env.local_path = PROJECT_ROOT
env.redis_version = "redis-1.02"

# ============   environments
class _server(object):
    """not used directly, for inheritance, defines base server"""
    _exclusions = ['desc']
    def __init__(self, *dconfigs, **kwargs):
        self.desc = "Server"
        for config in dconfigs:
            if type(config) is dict:
                for key in config:
                    setattr(self,key,config[key])
        for key in kwargs:
            setattr(self,key,kwargs[key])
        #self._envkeys = self.__dict__.keys
        self.__doc__ = self.desc
    
    def __call__(self):
        for key in self.__dict__.keys():
            if key not in _server._exclusions:
                setattr(env,key,self.__dict__[key])
        if hasattr(self,"host") and not self.host in env.hosts:
            env.hosts += [self.host]
    
    def __str__(self):
        return "%s" % self.__dict__
    


base_config = {
    "host"  : "localhost",
    "user" : "demisauce",
    "path" : "/home/demisauce",
    "desc" : "Default demisauce server",
    "os"   : "ubuntu9.04",
    "type" : 'vm',
    "environment" : 'dev',
    "mailhostname" : 'demisauce.org',
    "mysql_root_pwd": "demisauce",
}

# environments  ========================
vm106 = _server(base_config,{"desc":"VMware 106 Demisauce Server","host"  : "192.168.0.106"})
vm107 = _server(base_config,{"desc":"VMware 107 Demisauce Server","host"  : "192.168.0.107"})
ec2prod = _server(base_config,{"desc":"EC2 Prod 1","host"  : "aws.amazon.com","mailhostname" : 'smtp.demisauce.org'})
imac = _server(base_config,{"desc":"iMac Desktop Dev", "os": "osx", "host"  : "localhost","user":"aaron"})

#print "\nvm106 = %s" % vm106
#print "\nvm107 = %s" % vm107
"""{'mailhostname': 'localhost', 
    'show': None, 'key_filename': None, 'reject_unknown_hosts': False, 
    'project_name': 'demisauce', 'roledefs': {}, 'redis_version': 'redis-1.02', 
    'path_behavior': 'append', 'hide': None, 'sudo_prefix': "sudo -S -p '%s' ", 
    'host_string': '192.168.0.106', 'environment': 'dev', 'version': '1.0a0', 
    'command': 'db_backup_apply', 'fabfile': 'fabfile', 'type': 'vm', 'cwd': '', 
    'disable_known_hosts': False, 'real_fabfile': '/Users/aaron/Dropbox/demisauce/install/fabfile.py', 
    'shell': '/bin/bash -l -c', 'always_use_pty': False, 'all_hosts': ['192.168.0.106'], 
    'sudo_prompt': 'sudo password:', 'again_prompt': 'Sorry, try again.\n', 
    'host': '192.168.0.106', 'port': '22', 'user': 'demisauce', 'path': '/home/demisauce', 
    'password': 'xyz', 'rcfile': '/Users/aaron/.fabricrc', 'desc': 'VMware 106 Demisauce Server', 
    'roles': [], 'local_path': '/Users/aaron/Dropbox/demisauce', 'use_shell': True, 
    'hosts': ['192.168.0.106'], 'mysql_root_pwd': 'demisauce', 'warn_only': False, 'os': 'ubuntu9.04'} """

def _vm106():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.106']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu9.04'
    env.type = 'vm'
    env.environment = 'dev'
    env.mailhostname = 'demisauce106.localhost'

def _vm107():
    "The dev VM linux machine"
    env.hosts = ['192.168.0.107']
    env.user = 'demisauce'
    env.path = '/home/demisauce' 
    env.os = 'ubuntu9.04'
    env.type = 'vm'
    env.environment = 'prod'
    env.mailhostname = 'demisauce107.localhost'


# ===== Private Tasks ==========
def _nginx_release():
    sudo("/etc/init.d/nginx stop")
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        with cd("/etc/nginx"):
            sudo("rm nginx.conf")
            sudo("rm sites-enabled/demisauce;")
            sudo("rm sites-enabled/defaultmd5")
    put('%s/nginx/nginx.conf' % INSTALL_ROOT, '/tmp/nginx.conf')
    put('%s/nginx/sites-enabled/demisauce' % INSTALL_ROOT, '/tmp/sa-ds')
    sudo('mv /tmp/nginx.conf /etc/nginx/nginx.conf')
    sudo('mv /tmp/sa-ds /etc/nginx/sites-enabled/demisauce')

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
    setting alias maps
    setting alias database
    mailname is not a fully qualified domain name.  Not changing /etc/mailname.
    setting destinations: /etc/mailname, demisauce, localhost.localdomain, localhost
    setting relayhost: 
    setting mynetworks: 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
    setting mailbox_size_limit: 0
    setting recipient_delimiter: +
    setting inet_interfaces: all
    """
    require('mailhostname', provided_by=[vm107,vm106,ec2prod])
    put('%(local_path)s/install/install_zamanda.sh' % env, '/tmp/install_zamanda.sh' % env)
    sudo('chmod +x /tmp/install_zamanda.sh; /tmp/install_zamanda.sh %s %s %s' % (mysqlpwd,mysqlpwd,env.type))
    sudo('rm /tmp/install_zamanda.sh')
    sudo('echo "%(mailhostname)s" >> /etc/mailname' % env)

def _nginx():
    """Installs Nginx"""
    sudo("""echo "deb http://ppa.launchpad.net/jdub/devel/ubuntu hardy main" >> /etc/apt/sources.list
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E9EEF4A1""")
    sudo("apt-get -y update; apt-get -y install nginx")
    #get('/etc/nginx/mime.types', '%s/nginx/mime.types' % INSTALL_ROOT)
    #get('/etc/nginx/nginx.conf', '%s/nginx/nginx.conf' % INSTALL_ROOT)
    sudo("mkdir -p /vol/log/nginx")

def _gearmanDrizzle():
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
    
    sudo("apt-get -y update; apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 06899068")
    sudo("apt-get -y update; apt-get install -y gearman gearman-job-server gearman-tools libgearman2 libgearman-dev libgearman-dbg libgearman-doc")

def _gearman():
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
    
    sudo("apt-get -y --force-yes update")
    sudo("apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1C73E014")

def _gearman_step2():
    """you need to manually update key before this
    because it keeps !#%!#$ timing out"""
    sudo("apt-get -y update")
    sudo("apt-get install -y gearman gearman-job-server gearman-tools libgearman2 libgearman-dev libgearman-dbg libgearman-doc")

def _linux_base():
    """Installs base Linux essentials (ubuntu install)"""
    """
    First you have installed base ubuntu and ssh, wget:
    sudo apt-get -y update; sudo apt-get -y install openssh-server wget
    """
    sudo("apt-get -y update; apt-get -y install wget unzip cron rsync python-setuptools python-dev")
    sudo("apt-get -y install build-essential git-core; apt-get -y update")
    sudo("easy_install -U pip")

def _demisauce_pre_reqs():
    """install python-mysqldb, gdata, boto(amazon api's)"""
    sudo('apt-get -y install python-mysqldb')
    sudo('easy_install http://gdata-python-client.googlecode.com/files/gdata.py-1.1.1.tar.gz')
    sudo('easy_install http://boto.googlecode.com/files/boto-1.8d.tar.gz')

#   Tasks   =======================
def release(userdbpwd):
    'Deploy a new/updated release to the target environment'
    _nginx_release()
    with settings(hide('warnings', 'running', 'stdout', 'stderr'),warn_only=True):
        sudo("rm /home/demisauce/ds/current; rm /home/demisauce/ds/current_web")
    release = datetime.datetime.now().strftime("%Y%m%d%H")
    sudo("mkdir -p /home/demisauce/ds/%s" % release)
    sudo("chown -R demisauce:demisauce /home/demisauce/ds")
    rsync_project('/home/demisauce/ds/%s/' % release,local_dir='%(local_path)s/' % env)
    sudo('ln -s /home/demisauce/ds/%s/demisauce/trunk /home/demisauce/ds/current_web' % (release))
    sudo('ln -s /home/demisauce/ds/%s/ /home/demisauce/ds/current' % (release))
    
    put('%(local_path)s/install/install_demisauce.sh' % env, '/tmp/install_demisauce.sh' % env)
    sudo('chmod +x /tmp/install_demisauce.sh; /tmp/install_demisauce.sh install -d %s -p %s -r %s -e %s -s local' % \
            ("/home/demisauce/ds",userdbpwd,env.environment,env.type))
    sudo('rm /tmp/install_demisauce.sh')
    
    sudo("/etc/init.d/nginx restart")

def db_backup_apply():
    """Apply a backup """
    require("mysql_root_pwd")
    sudo("mysql -uroot -pdemisauce < /home/demisauce/ds/current/backup-file.sql ")

def release_nginx():
    """Updates nginx config, and restarts
    
    fab vm107 release_nginx -p demisauce
    """
    _nginx_release()
    sudo("/etc/init.d/nginx restart")

def restart_web():
    """restarts nginx, and demisauce python app"""
    sudo("/etc/init.d/demisauce_web restart")
    sudo("/etc/init.d/nginx restart")

def ec2_save_image():
    """Takes an instance on EC2 and saves to S3"""
    raise NotImplemented("needs to be done")

def db_sqldump(pwd):
    """Takes a full sql dump"""
    sudo("mysqldump -uroot -p%s demisauce > backup-file.sql" % pwd)

def build_step1(rootmysqlpwd="demisauce",userdbpwd="demisauce"):
    """Build base demisauce linux install, then manually run::
        apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1C73E014
        as it will timeout
    """
    require('hosts', provided_by=[vm107,vm106,ec2prod])
    _linux_base()
    _gearman()

def build_step2(rootmysqlpwd="demisauce",userdbpwd="demisauce"):
    """Step two updating keys, installs gearman,mysql,memcached,nginx, python dependencies"""
    require('hosts', provided_by=[vm107,vm106,ec2prod])
    _gearman_step2()
    _memcached()
    _mysql(rootmysqlpwd,userdbpwd)
    _zamanda(userdbpwd)
    _nginx()
    _demisauce_pre_reqs()


