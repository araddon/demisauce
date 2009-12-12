"""
    see documentaiton:  http://github.com/araddon/demisauce/tree/master/install
"""
from __future__ import with_statement # needed for python 2.5
from fabric.api import *
from fabric.contrib.project import rsync_project
import os, simplejson, datetime

# TODO:  build a bootstrap.sh that installs fab, uses local ip, runs this inside vm
# TODO:  convert paster/ds over to supervisord
# TODO /etc/init.d/demisauce_web is owned by demisauce instead of root
# TODO persistent state?   between runs?  couchdb?  json file on server?

# =============    globals
env.project_name = 'demisauce'
INSTALL_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.realpath(INSTALL_ROOT + '/../' )
env.path = "/home/demisauce"
env.local_path = PROJECT_ROOT
env.redis_version = "redis-1.02"
env.keys_added = False

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
    "ip"    : "192.168.0.1",
    "user" : "demisauce",
    "path" : "/home/demisauce",
    "desc" : "Default demisauce server",
    "os"   : "ubuntu9.10",
    "type" : 'vm',
    "environment" : 'dev',
    "mailhostname" : 'demisauce.org',
    "mysql_root_pwd": "demisauce",
}
vmlocal = _server(base_config,{"desc":"LocalHost","host"  : "127.0.0.1", "ip":"127.0.0.1"})
d6 = _server(base_config,{"desc":"VMware 115 Demisauce Server","host"  : "192.168.0.115", "ip":"192.168.0.115"})
d5 = _server(base_config,{"desc":"KVM 1.9 Demisauce Server","host"  : "192.168.1.9", "ip":"192.168.1.9"})
d4 = _server(base_config,{"desc":"KVM 1.7 Demisauce Server","host"  : "192.168.1.7", "ip":"192.168.1.7"})
s1 = _server(base_config,{"desc":"KVM 1.5 Demisauce Solr Server","host"  : "192.168.1.5", "ip":"192.168.1.5"})
s2 = _server(base_config,{"desc":"KVM Demisauce Solr Server","host"  : "192.168.1.14", "ip":"192.168.1.14"})
ec2prod = _server(base_config,{"desc":"EC2 Prod 1","host"  : "aws.amazon.com",
    "mailhostname" : 'smtp.demisauce.org', "ip":"192.168.0.112"})
imac = _server(base_config,{"desc":"iMac Desktop Dev", "os": "osx", "host"  : "localhost","user":"aaron"})
ubuntu1 = _server(base_config,{"desc":"HP Ubuntu Desktop", "host"  : "192.168.1.4","user":"aaron"})

"""list of dir(env)
    {'mailhostname': 'localhost', 
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
    'hosts': ['192.168.0.106'], 'mysql_root_pwd': 'demisauce', 'warn_only': False, 'os': 'ubuntu9.04'} 
"""
# ===== Private Tasks ==========
def _nginx_release():
    sudo("/etc/init.d/nginx stop")
    with settings(hide('warnings', 'stderr'),warn_only=True):
        sudo("rm /etc/nginx/sites-enabled/default")
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        with cd("/etc/nginx"):
            sudo("rm nginx.conf")
            sudo("rm sites-enabled/demisauce;")
    put('%s/recipes/etc/nginx/nginx.conf' % INSTALL_ROOT, '/tmp/nginx.conf')
    put('%s/recipes/etc/nginx/sites-enabled/demisauce' % INSTALL_ROOT, '/tmp/sa-ds')
    sudo('mv /tmp/nginx.conf /etc/nginx/nginx.conf')
    sudo('mv /tmp/sa-ds /etc/nginx/sites-enabled/demisauce')

def _memcached():
    sudo("apt-get install --yes --force-yes -q memcached")
    print("SECURITY NOTICE:  Enabling memcached from remote")
    #comment out line for -l 127.0.0.1 which restricts to only local machine
    sudo("rm /etc/default/memcached") # new file synced over in build rsync
    sudo('perl -pi -e s/-l\ 127.0.0.1/\#-l\ 127.0.0.1/g /etc/memcached.conf')

def _mysql(rootmysqlpwd,mysqlpwd):
    put('%(local_path)s/install/install_mysql.sh' % env, '/tmp/install_mysql.sh' % env)
    sudo('chmod +x /tmp/install_mysql.sh; /tmp/install_mysql.sh %s %s %s' % (rootmysqlpwd,mysqlpwd,env.type))
    sudo('rm /tmp/install_mysql.sh')
    if env.environment == 'dev':
        """mysql -u[user] -p[pass] <<QUERY_INPUT
        [mysql commands]
        QUERY_INPUT
        or
        mysql -u[user] -p[pass] -e"use mysql;  select * from user;"  """
        run("""mysql -uroot -p%(pwd)s <<QUERY_INPUT
            use mysql; 
            update user set host = '%(host)s' where user = 'ds_web' and host = 'localhost';
            \nQUERY_INPUT""" % ({'pwd':'demisauce', 'host':'%'}))
        
        sudo('perl -pi -e "s/127.0.0.1/127.0.0.1\nbind-address = %s\n/g" /etc/mysql/my.cnf' % (env.ip))
        sudo('/etc/init.d/mysql restart')

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
    put('%(local_path)s/install/install_zamanda.sh' % env, '/tmp/install_zamanda.sh' % env)
    sudo('chmod +x /tmp/install_zamanda.sh; /tmp/install_zamanda.sh %s %s %s' % (mysqlpwd,mysqlpwd,env.type))
    sudo('rm /tmp/install_zamanda.sh')
    #sudo('echo "%(mailhostname)s" >> /etc/mailname' % env)

def _postfix():
    """Install Postfix mail server"""
    sudo('mkdir -p /etc/postfix')
    put('%s/recipes/etc/postfix/main.cf' % INSTALL_ROOT, '/tmp/main.cf')
    sudo('mv /tmp/main.cf /etc/postfix/main.cf')
    sudo('echo "%(mailhostname)s" >> /etc/mailname' % env)
    sudo("env DEBIAN_FRONTEND=noninteractive apt-get -y install postfix")
    
    # These are all the options, but we only use a couple above
    #  http://reductivelabs.com/trac/puppet/wiki/Recipes/DebianPreseed
    """postfix postfix/root_address    string  
        postfix postfix/rfc1035_violation   boolean false
        postfix postfix/mydomain_warning    boolean 
        postfix postfix/mynetworks  string  127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
        postfix postfix/mailname    string  demisauce.org
        postfix postfix/tlsmgr_upgrade_warning  boolean 
        postfix postfix/recipient_delim string  +
        postfix postfix/main_mailer_type    select  Internet Site
        postfix postfix/destinations    string  demisauce.org, demisauce, localhost.localdomain, localhost
        postfix postfix/retry_upgrade_warning   boolean 
        postfix postfix/kernel_version_warning  boolean 
        postfix postfix/not_configured  error   
        postfix postfix/mailbox_limit   string  0
        postfix postfix/relayhost   string  
        postfix postfix/procmail    boolean false
        postfix postfix/bad_recipient_delimiter error   
        postfix postfix/protocols   select  all
        postfix postfix/chattr  boolean false
    """

def _nginx():
    """Installs Nginx"""
    sudo("apt-get -y update; apt-get -y install nginx")
    #get('/etc/nginx/mime.types', '%s/nginx/mime.types' % INSTALL_ROOT)
    #get('/etc/nginx/nginx.conf', '%s/nginx/nginx.conf' % INSTALL_ROOT)
    sudo("rm /etc/nginx/sites-enabled/default")
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

def _gearman_sources():
    """Adds sources for gearman, tries to get key"""
    # sources for gearman
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
    

def _gearman():
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
    sudo("apt-get -y update; apt-get -y install wget unzip cron rsync python-setuptools python-dev python-virtualenv")
    sudo("apt-get -y install build-essential git-core mercurial; apt-get -y update")
    sudo("easy_install -U pip")

def _demisauce_pre_reqs():
    """install python-mysqldb, gdata, boto(amazon api's), solr, oauth"""
    sudo("mkdir -p /home/demisauce/lib")
    
    with cd("/home/demisauce/lib"):
        
        sudo("git clone git://github.com/leah/python-oauth.git oauth")
        with cd("oauth"):
            sudo("python setup.py install")
        
        sudo("git clone git://github.com/araddon/redis-py.git")
        with cd("redis-py"):
            sudo("python setup.py install")
        
        sudo("hg clone http://bitbucket.org/araddon/python-solr/")
        with cd("python-solr"):
            sudo("python setup.py install")
        
        sudo('apt-get -y install python-mysqldb python-memcache')
        sudo('apt-get -y install python-imaging')  # imaging library for image resize
        sudo('easy_install http://gdata-python-client.googlecode.com/files/gdata.py-1.1.1.tar.gz')
        sudo('easy_install http://boto.googlecode.com/files/boto-1.8d.tar.gz')
        sudo('easy_install http://www.crummy.com/software/BeautifulSoup/download/3.x/BeautifulSoup-3.1.0.tar.gz')
        sudo("apt-get install -y libgearman2")
        sudo('pip install http://github.com/samuel/python-gearman/tarball/master')
        sudo("pip install http://github.com/samuel/python-scrubber/tarball/master")

def _exists(path):
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        if run("[ -d %s ] && echo $? " % path) == '0':
            return True
        else:
            #run('ls /etc/redhat-release'):
            return False

def _redis_restart():
    if run('ps -A | grep redis-server'):
        print("Redis already running ")
        # this doesn't work, try the init-functions 
        #sudo("kill `ps -A | grep redis-server | cut -b2-5`")
    else:
        if run('ls /var/run | grep redis.pid'):
            # dead pid file
            sudo("rm /var/run/redis.pid")
    # run the server
    sudo('/opt/%(redis_version)s/redis-server %(path)s/redis/redis.conf' % env)

def _redis_install():
    """install redis"""
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        if not run('ls /opt | grep %(redis_version)s' % env):
            with cd("/opt"):
                print("----  installing redis   ----------")
                sudo("wget http://redis.googlecode.com/files/redis-1.02.tar.gz; tar xvzf redis*.tar.gz")
                sudo("rm redis*.tar.gz; cd redis*; make")
        with cd('/vol'): #/home/demisauce
            if not run('ls | grep redis'):
                sudo('mkdir -p redis', pty=True)
            if not run('ls redis | grep data'):
                sudo('mkdir -p redis/data', pty=True)
                sudo('chown demisauce redis')

def _redis_conf_update():
    put('%(local_path)s/install/recipes/vol/redis/redis.conf' % env, '/vol/redis/redis.conf')

def _supervisord_install():
    sudo("easy_install supervisor")
    

def _install_solr():
    "install solr"
    #http://justin-hayes.com/2009-04-08/installing-apache-tomcat-6-and-solr-nightly-on-ubuntu-804
    sudo("apt-get install -y default-jdk default-jre") 
    with cd("/tmp"):
        sudo("rm -rf *")
        run("wget http://mirror.its.uidaho.edu/pub/apache/lucene/solr/1.4.0/apache-solr-1.4.0.tgz")
        run("wget http://www.alliedquotes.com/mirrors/apache/tomcat/tomcat-6/v6.0.20/bin/apache-tomcat-6.0.20.tar.gz")
        run("tar xfzv apache-solr-1.4.0.tgz")
        run("tar xfzv apache-tomcat-6.0.20.tar.gz")
        sudo("mv apache-tomcat-6.0.20/ /usr/local/tomcat6/")
        sudo("cp apache-solr-1.4.0/dist/apache-solr-1.4.0.war /usr/local/tomcat6/webapps/dssolr.war")
        sudo("cp -r apache-solr-1.4.0/example/solr/ /usr/local/tomcat6/dssolr/")
    sudo("mkdir -p /usr/local/tomcat6/conf/Catalina/localhost/")
    sudo("""cat <<EOL > /usr/local/tomcat6/conf/Catalina/localhost/dssolr.xml
<Context docBase="/usr/local/tomcat6/webapps/dssolr.war" debug="0" crossContext="true" >
    <Environment name="solr/home" type="java.lang.String" value="/usr/local/tomcat6/dssolr" override="true" />
</Context>
EOL
""")
    sudo("rsync  -pthrvz  /vol/solr/conf /usr/local/tomcat6/dssolr/")
    sudo("rsync  -pthrvz  /home/demisauce/etc /") 
    sudo("chmod 755 /etc/init.d/tomcat6")
    sudo("sudo update-rc.d tomcat6 start 91 2 3 4 5 . stop 20 0 1 6 .")
    sudo("/etc/init.d/tomcat6 start")


#   Tasks   =======================
def _x_supervisor_update():
    """Refresh conf file for supervisord, restart"""
    put('%(local_path)s/install/recipes/etc/supervisord.conf' % env, '/tmp/supervisord.conf' % env)
    sudo('mv /tmp/supervisord.conf /etc/supervisord.conf')
    #sudo('/usr/local/bin/supervisord')
    sudo('/etc/init.d/supervisord restart')

def add_sources():
    """This often times out, so run it first"""
    # sources for nginx
    sudo('echo "deb http://ppa.launchpad.net/jdub/devel/ubuntu hardy main" >> /etc/apt/sources.list')
    #sudo("""echo "deb http://ppa.launchpad.net/jdub/devel/ubuntu hardy main" >> /etc/apt/sources.list
    #    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E9EEF4A1""")
    _gearman_sources()
    
    with settings(hide('warnings'),warn_only=True):
        # key for nginx
        keeptrying, attempt = True, 1
        while keeptrying == True:
            print("about to try to get key, may take a while or time out, attempt #%s" % attempt)
            attempt += 1
            output = sudo("apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1C73E014")
            #print("just ran, .failed = %s, .return_code = %s,  string=%s" % (output.failed,output.return_code,output))
            keeptrying = output.failed
        
        # key for gearman
        keeptrying, attempt = True, 1
        while keeptrying == True:
            print("about to try to get key, may take a while or time out, attempt #%s" % attempt)
            attempt += 1
            output = sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E9EEF4A1')
            #print("just ran, .failed = %s, .return_code = %s,  string=%s" % (output.failed,output.return_code,output))
            keeptrying = output.failed # if failed = True, keep trying
            
    env.keys_added = True
    
    # do update before getting keys
    sudo("apt-get -y --force-yes update")

def release(userdbpwd="demisauce"):
    'Deploy a new/updated demisauce web release to the target server'
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

def simple_push():
    """Simple release, just web sync, no new folders"""
    rsync_project('/home/demisauce/ds/current_web/',local_dir='%(local_path)s/demisauce/trunk/' % env)
    restart_web()

def sync_etc():
    """Configuration Sync"""
    sudo("mkdir -p /vol; chown -R demisauce:demisauce /vol")
    rsync_project('/home/demisauce/',local_dir='%(local_path)s/install/recipes/etc' % env)
    rsync_project('/vol/',local_dir='%(local_path)s/install/recipes/vol/' % env)

def db_backup_apply():
    """Apply a backup """
    require("mysql_root_pwd")
    print("Mysql_root_pwd = %s" % env.mysql_root_pwd)
    #sudo("mysql -uroot -p%(mysql_root_pwd)s < /home/demisauce/ds/current/backup-file.sql " % env)

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

def build(rootmysqlpwd="demisauce",userdbpwd="demisauce",host=None):
    """base linux install, then manually run::
        apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1C73E014
        as it will timeout
    """
    if host:
        env.host = host
    sudo("apt-get -y install rsync")
    
    sync_etc() # do this first to force rsynch/ssh pwd at beginning to it doesn't 255 error timeout
    
    add_sources()
    _linux_base()
    # this would only work if we have a more persistent "state" across runs
    #if not env.keys_added:
    #    print("You need to run add_sources first, as it times out quite often we do that first in case it times out")
    #    return
    _gearman()
    _memcached()
    _postfix()# must be installed before zamanda which installs it in interactive mode
    _mysql(rootmysqlpwd,userdbpwd)
    _zamanda(userdbpwd)
    _nginx()
    _demisauce_pre_reqs()
    _redis_install()
    _redis_conf_update()
    _supervisord_install()
    _install_solr()
    # move from temp home to /etc
    sudo("rsync  -pthrvz  /home/demisauce/etc /") 
    #supervisor_update() # also starts supervisord
    sudo('/etc/init.d/supervisord restart')
    sudo('sudo update-rc.d supervisord defaults')

def all(rootmysqlpwd="demisauce",userdbpwd="demisauce"):
    """Build AND Release"""
    build(rootmysqlpwd=rootmysqlpwd,userdbpwd=userdbpwd)
    release(userdbpwd=userdbpwd)

def build_solr(rootmysqlpwd="demisauce",userdbpwd="demisauce"):
    """Build a solr server"""
    sudo("apt-get -y install rsync")
    sync_etc() # do this first to force rsynch/ssh pwd at beginning to it doesn't 255 error timeout
    
    add_sources()
    _linux_base()
    _install_solr()

def install_dev():
    "install on dev linux machine"
    sudo("apt-get -y install rsync")
    add_sources()
    _linux_base()
    _demisauce_pre_reqs()
    

def solr_conf():
    """Configuration Sync"""
    rsync_project('/vol/',local_dir='%(local_path)s/install/recipes/vol/' % env)
    sudo("rsync  -pthrvz  /vol/solr/conf /usr/local/tomcat6/dssolr/")
    sudo("/etc/init.d/tomcat6 restart")




