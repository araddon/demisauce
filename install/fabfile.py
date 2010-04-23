"""
    see documentaiton:  http://github.com/araddon/demisauce/tree/master/install
"""
from fabric.api import *
from fabric.contrib.project import rsync_project
import os, json, datetime, time
from string import Template

# TODO =================================
# convert to ssh keys on local dev machines not just ec2
# mysql ip binding  Needed?  remove?
# ec2 wants to restart?
# convert to chef or kokki?
# mysql isn't reachable from remote because of permissions in db
# =============    globals
INSTALL_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.realpath(INSTALL_ROOT + '/../' )
USER_HOME = os.path.realpath('../../../')
#env.keys_added = False
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
    "project_name" : 'demisauce',
    "ip"    : "127.0.0.1",
    "redis_version":'redis-1.02',
    "user" : "demisauce",
    "path" : "/home/demisauce",
    "desc" : "Default demisauce server",
    "os"   : "ubuntu9.10",
    "type" : 'vm',
    "local_path": PROJECT_ROOT,
    "user_home": USER_HOME,
    "environment" : 'dev',
    "mailhostname" : 'demisauce.org',
    "mysql_root_pwd": "demisauce",
    "mysql_user":'ds_web',
    "mysql_user_pwd":'demisauce',
    "smtp_pwd": 'yourpwd',
    "ds_api_key":'a95c21ee8e64cb5ff585b5f9b761b39d7cb9a202',
    "ds_url":'http://localhost:4950',
    "ds_domain":"localhost",
    "recipes":['wp','solr','redis','gearman','mysql','demisauce','postfix']
}
vmlocal = _server(base_config,{"desc":"LocalHost","host"  : "127.0.0.1", "ip":"127.0.0.1"})
d1 = _server(base_config,{"desc":"Your VM/KVM Demisauce server","host"  : "192.168.1.15", "ip":"192.168.1.15"})
ec2 = _server(base_config,{"desc":"EC2 Dev Trial Env",'user':'ubuntu','type':'ec2',
    "host"  : "ec2.your.ip.from.amazon.amazonaws.com",
    "mailhostname" : 'smtp.demisauce.org', "ip":"127.0.0.1", 
    'key_filename': '%s/.ec2/id_rsa' % base_config['user_home'], 
    'ec2instance':'i-1111111','ec2volume':'vol-a0111111',
    'ec2zone':'us-east-1a','env':'prod'})

try:
    # if you want private recipes to include
    from privatefab import *
except ImportError:
    pass

#from subprocess import PIPE, Popen
#o = Popen("ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}'",shell=True,stdout=PIPE).communicate()[0].strip()

# ===== Private Tasks ==========
def _nginx_release():
    with settings(hide('warnings', 'stderr'),warn_only=True):
        sudo("rm /etc/nginx/sites-enabled/default")
        sudo("rm /tmp/wordpress.conf; rm /tmp/demisauce; rm /tmp/nginx.conf")
    with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
        with cd("/etc/nginx"):
            sudo("rm nginx.conf")
            sudo("rm sites-enabled/demisauce;")
            sudo("rm sites-enabled/wordpress")
            
    put('%s/recipes/etc/nginx/nginx.conf' % INSTALL_ROOT, '/tmp/nginx.conf')
    if 'wp' in env['recipes']:
        put('%s/recipes/etc/nginx/sites-enabled/wordpress.conf' % INSTALL_ROOT, '/tmp/wordpress.conf')
        sudo('mv /tmp/wordpress.conf /etc/nginx/sites-enabled/wordpress.conf')
    put('%s/recipes/etc/nginx/sites-enabled/demisauce' % INSTALL_ROOT, '/tmp/demisauce')
    sudo('mv /tmp/nginx.conf /etc/nginx/nginx.conf')
    sudo('mv /tmp/demisauce /etc/nginx/sites-enabled/demisauce')

def _memcached():
    sudo("apt-get install --yes --force-yes -q memcached")
    print("SECURITY NOTICE:  Enabling memcached from remote")
    #comment out line for -l 127.0.0.1 which restricts to only local machine
    with settings(hide('warnings', 'stderr'),warn_only=True):
        sudo("rm /etc/default/memcached") # new file synced over in build rsync
        sudo('perl -pi -e s/-l\ 127.0.0.1/\#-l\ 127.0.0.1/g /etc/memcached.conf')
    sudo("sudo update-rc.d memcached start 91 2 3 4 5 . stop 20 0 1 6 .")
    sudo('/etc/init.d/memcached start')

def _mysql():
    put('%(local_path)s/install/install_mysql.sh' % env, '/tmp/install_mysql.sh' % env)
    sudo('chmod +x /tmp/install_mysql.sh; /tmp/install_mysql.sh %(mysql_root_pwd)s %(mysql_user_pwd)s %(type)s' % (env))
    sudo('rm /tmp/install_mysql.sh')
    if env.environment == 'dev':
        """mysql -u[user] -p[pass] <<QUERY_INPUT
        [mysql commands]
        QUERY_INPUT
        or
        mysql -u[user] -p[pass] -e"use mysql;  select * from user;"  """
        run("""mysql -uroot -p%(mysql_root_pwd)s <<QUERY_INPUT
            use mysql; 
            update user set host = '%(host)s' where user = 'ds_web' and host = 'localhost';
            \nQUERY_INPUT""" % ({'mysql_root_pwd':'%s' % env.mysql_root_pwd, 'host':'%'}))
        
        sudo('perl -pi -e "s/127.0.0.1/127.0.0.1\nbind-address = %s\n/g" /etc/mysql/my.cnf' % (env.ip))
        sudo('/etc/init.d/mysql restart')

def _zamanda():
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
    sudo('chmod +x /tmp/install_zamanda.sh; /tmp/install_zamanda.sh %(mysql_root_pwd)s %(mysql_user_pwd)s %(type)s' % (env))
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
    sudo("apt-get -y install libgeoip-dev")
    #get('/etc/nginx/mime.types', '%s/nginx/mime.types' % INSTALL_ROOT)
    #get('/etc/nginx/nginx.conf', '%s/nginx/nginx.conf' % INSTALL_ROOT)
    with cd("/tmp"):
        run('wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz')
        run('gunzip GeoLiteCity.dat.gz')
        sudo('mv GeoLiteCity.dat /home/demisauce/GeoLiteCity.dat')
    sudo("rm /etc/nginx/sites-enabled/default")
    sudo("mkdir -p /vol/log/nginx")
    sudo("mkdir -p /var/www; chown -R www-data:www-data /var/www")

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
    sudo("apt-get install -y gearman gearman-job-server gearman-tools libgearman-dev libgearman-dbg libgearman-doc")

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
    sudo("chown -R %s:%s /home/demisauce/lib" % (env.user,env.user))
    sudo("chmod -R 770 /home/demisauce/lib")
    with cd("/home/demisauce/lib"):
        #rsync_project('/home/demisauce/lib/tornado/',local_dir='/Users/aaron/dev/tornado/')
        
        run("git clone git://github.com/araddon/tornado.git")
        with cd("tornado"):
            sudo("python setup.py build; python setup.py install")
        
        run("git clone git://github.com/ptarjan/python-oauth.git oauth")
        with cd("oauth"):
            sudo("python setup.py install")
            
        run("git clone git://github.com/sciyoshi/pyfacebook.git")
        with cd("oauth"):
            sudo("python setup.py install")
        
        run("git clone git://github.com/araddon/redis-py.git")
        with cd("pyfacebook"):
            sudo("python setup.py install")
        
        run("hg clone http://bitbucket.org/araddon/python-solr/")
        with cd("python-solr"):
            sudo("python setup.py install")
        
        sudo("pip install avro")
        sudo("apt-get -y install python-dev python-pycurl") # ?  should be part of python  python-json
        sudo('apt-get -y install python-mysqldb python-memcache')
        sudo('apt-get -y install python-imaging')  # imaging library for image resize
        sudo('easy_install http://gdata-python-client.googlecode.com/files/gdata.py-1.1.1.tar.gz')
        sudo('easy_install http://boto.googlecode.com/files/boto-1.8d.tar.gz')
        sudo('easy_install http://www.crummy.com/software/BeautifulSoup/download/3.x/BeautifulSoup-3.1.0.tar.gz')
        # this needs to be removed once all formencode is removed. soon!
        sudo("easy_install formencode")
        #sudo("apt-get install -y libgearman2")
        sudo("easy_install python-libgearman")
        sudo("easy_install eventlet")
        sudo('pip install http://github.com/samuel/python-gearman/tarball/master')
        sudo("pip install http://github.com/samuel/python-scrubber/tarball/master")
        sudo("pip install Jinja2")
        sudo("pip install wtforms")
        sudo("pip install decorator")
        sudo("pip install feedparser")
        sudo("pip install http://python-twitter.googlecode.com/files/python-twitter-0.6.tar.gz")

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
                sudo("chmod -R 770 redis")

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
    

def _install_solr_war(name):
    'copies example war to given name'
    with cd("/tmp"):
        sudo("cp apache-solr-1.4.0/dist/apache-solr-1.4.0.war /usr/local/tomcat6/webapps/%s.war" % (name))
        sudo("cp -r apache-solr-1.4.0/example/solr/ /usr/local/tomcat6/%s/" % (name))
    sudo("mkdir -p /usr/local/tomcat6/conf/Catalina/localhost/")
    sudo("""cat <<EOL > /usr/local/tomcat6/conf/Catalina/localhost/%s.xml
<Context docBase="/usr/local/tomcat6/webapps/%s.war" debug="0" crossContext="true" >
    <Environment name="solr/home" type="java.lang.String" value="/usr/local/tomcat6/%s" override="true" />
</Context>
EOL
""" % (name,name,name))
    sudo("rsync  -pthrvz  /vol/solr/conf /usr/local/tomcat6/%s/" % (name))
    sudo("rsync  -pthrvz /home/demisauce/src/demisauce/install/recipes/etc /") 
    sudo("chmod 755 /etc/init.d/tomcat6")
    sudo("sudo update-rc.d tomcat6 start 91 2 3 4 5 . stop 20 0 1 6 .")
    sudo("/etc/init.d/tomcat6 start")
    


def _solr_spatial(name="dssolr"):
    'install solr spatial search'
    #http://craftyfella.blogspot.com/2009/12/installing-localsolr-onto-solr-14.html
    with cd("/tmp"):
        sudo("rm -rf *")
        run("wget http://www.nsshutdown.com/solr-example.tgz")
        run("tar xfzv solr-example.tgz")
        sudo("mv /tmp/solr-example/apache-solr-1.4.0/example/solr/lib/lucene-spatial-2.9.1.jar  /usr/local/tomcat6/webapps/%s/WEB-INF/lib/" % name)
        sudo("mv /tmp/solr-example/apache-solr-1.4.0/example/solr/lib/localsolr.jar  /usr/local/tomcat6/webapps/%s/WEB-INF/lib/" % name)

def _install_ds():
    "Installs Demisauce From Source"
    with cd("/home/demisauce/ds/current"):
        with cd("demisaucepy"):
            sudo("python setup.py develop")
    with cd("/home/demisauce/ds/current/plugins/py"):
        sudo("python setup.py develop")
    with cd("/home/demisauce/ds/web"):
        sudo("python setup.py develop")
        run("python manage.py --action=create_data --config=./demisauce.conf")
        run("python manage.py --action=updatesite --config=./demisauce.conf")
    
    sudo("mkdir -p /var/www/ds/static/upload")
    sudo("chown -R www-data:www-data /var/www")
    #sudo("chmod -R 770 /home/demisauce/ds")
        


def _wordpress_install():
    #http://nielsvz.com/2009/02/nginx-and-wordpress/
    #http://elasticdog.com/2008/02/howto-install-wordpress-on-nginx/
    # get fast-cgi module from lighttpd
    sudo("apt-get install -y -q lighttpd")
    #  php5-dev php5-ldap
    sudo("apt-get install --yes --force-yes -q php5-cli php5-cgi php5-memcache php5-gd php5-mysql ")
    # but don't start it, we just need the fast cgi module
    sudo("update-rc.d -f lighttpd remove")
    put('%(local_path)s/install/install_wordpress.sh' % env, '/tmp/install_wordpress.sh' % env)
    sudo('chmod +x /tmp/install_wordpress.sh; /tmp/install_wordpress.sh %(mysql_root_pwd)s %(mysql_user_pwd)s' % env)
    sudo('rm /tmp/install_wordpress.sh')
    sudo('chmod 777 /var/www/blog /var/www/blog/wp-content/ ')

def _wordpressmu_install():
    #http://nielsvz.com/2009/02/nginx-and-wordpress/
    #http://elasticdog.com/2008/02/howto-install-wordpress-on-nginx/
    # get fast-cgi module from lighttpd
    sudo("apt-get install -y -q lighttpd")
    #  php5-dev php5-ldap
    sudo("apt-get install --yes --force-yes -q php5-cli php5-cgi php5-memcache php5-gd php5-mysql ")
    # but don't start it, we just need the fast cgi module
    sudo("update-rc.d -f lighttpd remove")
    put('%(local_path)s/install/install_wordpressmu.sh' % env, '/tmp/install_wordpressmu.sh' % env)
    sudo('chmod +x /tmp/install_wordpressmu.sh; /tmp/install_wordpressmu.sh %(mysql_root_pwd)s %(mysql_user_pwd)s' % env)
    sudo('rm /tmp/install_wordpressmu.sh')

def _wordpress_updateconf():
    "update wordpress configuration on nginx, ini, supervisord etc"
    with settings(hide('warnings', 'stderr'),warn_only=True):
        with cd("/etc/nginx"):
            sudo("rm sites-enabled/wordpress.conf;")
            put('%s/recipes/etc/nginx/sites-enabled/wordpress.conf' % INSTALL_ROOT, '/tmp/wordpress.conf')
            sudo('mv /tmp/wordpress.conf /etc/nginx/sites-enabled/wordpress.conf')


#   Tasks   =======================
def fileconveyor():
    sudo("apt-get install python-pyinotify")

def update_config(mysql_user_pwd=None):
    'drops new config on said host'
    if mysql_user_pwd:
        env.mysql_user_pwd = mysql_user_pwd
    with settings(hide('warnings', 'stderr'),warn_only=True):
        sudo("rm -f /home/demisauce/ds/web/demisauce.conf")
    s = Template(open('%(local_path)s/demisauce/conf.tmpl' % env).read())
    run("echo '%s' > /home/demisauce/ds/web/demisauce.conf" % s.substitute(env))

def wordpress(mysql_root_pwd=None,mysql_user_pwd=None,standalone=False):
    "Install wordpress"
    if mysql_root_pwd:
        env.mysql_root_pwd = mysql_root_pwd
    if mysql_user_pwd:
        env.mysql_user_pwd = mysql_user_pwd
    if standalone:
        print("====== starting build ============")
        sudo("apt-get -y install rsync")
        sudo("mkdir -p /vol; chown -R %s:%s /vol" % (env.user,env.user))
        sudo("chmod -R 770 /vol")
        sudo("usermod -a -G www-data ubuntu; usermod -a -G www-data demisauce")
        add_sources()
        push_recipes() # do this first to force rsynch/ssh pwd at beginning to it doesn't 255 error timeout
        _linux_base()
        _mysql()
        _nginx()
    
    _wordpressmu_install()
    _wordpress_updateconf()
    if standalone:
        _supervisord_install()
        sudo("rsync  -pthrvz  /home/demisauce/src/demisauce/install/recipes/etc /") 
        sudo('/etc/init.d/supervisord restart')
        sudo('sudo update-rc.d supervisord defaults')
        sudo("/etc/init.d/nginx restart")
    
    print("don't forget to call release_nginx supervisor_update")

def dswp_plugin():
    rsync_project('/var/www/blog/wp-content/plugins/',local_dir='%(user_home)s/Dropbox/wordpress/wp-content/plugins/demisauce' % env)

def supervisor_update():
    """Refresh conf file for supervisord, restart"""
    put('%(local_path)s/install/recipes/etc/supervisord.conf' % env, '/tmp/supervisord.conf' % env)
    put('%(local_path)s/install/recipes/etc/supervisord/demisauce.conf' % env, '/tmp/demisauce_sd.conf' % env)
    sudo('mv /tmp/supervisord.conf /etc/supervisord.conf')
    sudo('mv /tmp/demisauce_sd.conf /etc/supervisord/demisauce.conf')
    #sudo('/usr/local/bin/supervisord')
    sudo('/etc/init.d/supervisord restart')

def add_sources():
    "adds ubuntu sources, does update"
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

def release(mysql_user_pwd=None,host=None,local=False):
    'Deploy a new/updated demisauce web release to the target server'
    if mysql_user_pwd:
        env.mysql_user_pwd = mysql_user_pwd
    _nginx_release()
    with settings(hide('warnings', 'running', 'stdout', 'stderr'),warn_only=True):
        sudo("rm /home/demisauce/ds/current; rm /home/demisauce/ds/web")
    
    local("cd %(local_path)s/demisauce; sh %(local_path)s/demisauce/jscss.sh" % env)
    release = datetime.datetime.now().strftime("%Y%m%d%H")
    sudo("mkdir -p /home/demisauce/ds/%s" % release)
    sudo("chown -R %s:%s /home/demisauce/ds" % (env.user,env.user))
    sudo("chmod -R 770 /home/demisauce/ds")
    rsync_project('/home/demisauce/ds/%s/' % release,local_dir='%(local_path)s/' % env)
    rsync_project('/var/www/blog/wp-content/plugins/',local_dir='%(user_home)s/wordpress/wp-content/plugins/demisauce' % env)
    sudo('ln -s /home/demisauce/ds/%s/demisauce /home/demisauce/ds/web' % (release))
    sudo('ln -s /home/demisauce/ds/%s/ /home/demisauce/ds/current' % (release))
    update_config()
    _install_ds()
    sudo("rsync  -pthrvz  /home/demisauce/ds/web/demisauce/static /var/www/ds") 
    sudo("chown -R www-data:www-data /var/www")
    sudo("chmod -R 775 /var/www")

def release_simple(mysql_user_pwd=None):
    if mysql_user_pwd:
        env.mysql_user_pwd = mysql_user_pwd
    """Simple release, just web and dspy sync, no new folders"""
    local("cd %(local_path)s/demisauce; sh %(local_path)s/demisauce/jscss.sh" % env)
    rsync_project('/home/demisauce/ds/current/demisaucepy/',local_dir='%(local_path)s/demisaucepy/' % env)
    rsync_project('/home/demisauce/ds/current/plugins/',local_dir='%(local_path)s/plugins/' % env)
    rsync_project('/home/demisauce/ds/web/',local_dir='%(local_path)s/demisauce/' % env)
    sudo("chown -R %s:%s /var/www/blog/wp-content/themes" % (env.user,env.user))
    rsync_project('/var/www/blog/wp-content/themes/',local_dir='%(user_home)s/Dropbox/wordpress/wp-content/themes/' % env)
    sudo("chown -R %s:%s /var/www/blog/wp-content/plugins" % (env.user,env.user))
    rsync_project('/var/www/blog/wp-content/plugins/',local_dir='%(user_home)s/Dropbox/wordpress/wp-content/plugins/demisauce' % env)
    sudo("rsync  -pthrvz  /home/demisauce/ds/web/demisauce/static /var/www/ds") 
    sudo("chown -R www-data:www-data /var/www")
    sudo("chmod -R 775 /var/www")
    update_config()
    restart_web()

def push_recipes(local=False):
    """Configuration Sync"""
    if local:
        pass # already retrieved from install.sh git clone
        rsync_project('/vol/',local_dir='%(local_path)s/install/recipes/vol/' % env)
    else:
        # in dev, get from dev machine
        sudo("mkdir -p /home/demisauce/src/demisauce/install/recipes/etc")
        sudo("chown -R %s:%s /home/demisauce" % (env.user,env.user))
        sudo("chmod -R 770 /home/demisauce")
        rsync_project('/home/demisauce/src/demisauce/install/recipes/etc/',local_dir='%(local_path)s/install/recipes/etc/' % env)
        rsync_project('/vol/',local_dir='%(local_path)s/install/recipes/vol/' % env)
    

def db_backup_apply(mysql_root_pwd=None):
    """Apply a backup """
    if mysql_root_pwd:
        env.mysql_root_pwd = mysql_root_pwd
    sudo("rm -f /tmp/*.sql")
    put('%s/demisaucedb.sql' % PROJECT_ROOT, '/tmp/demisaucedb.sql')
    #put('%s/wordpressdb.sql' % PROJECT_ROOT, '/tmp/wordpressdb.sql')
    sudo("mysql -uroot -p%(mysql_root_pwd)s < /tmp/demisaucedb.sql " % env)
    #sudo("mysql -uroot -p%(mysql_root_pwd)s < /tmp/wordpressdb.sql " % env)
    sudo("rm /tmp/*.sql")

def release_nginx():
    """Updates nginx config, and restarts"""
    _nginx_release()
    sudo("/etc/init.d/nginx reload")

def restart_web():
    """restarts nginx, and demisauce python app"""
    sudo("supervisorctl restart demisauce")
    sudo("supervisorctl restart dspygearman")

def ec2_save_image():
    """Takes an instance on EC2 and saves to S3"""
    raise NotImplemented("needs to be done")

def db_sqldump(mysql_root_pwd=None):
    """Takes a full sql dump"""
    if mysql_root_pwd:
        env.mysql_root_pwd = mysql_root_pwd
    sudo("mysqldump -uroot -p%(mysql_root_pwd)s demisauce > /tmp/demisaucedb.sql" % env)
    #sudo("mysqldump -uroot -p%(mysql_root_pwd)s wordpress > /tmp/wordpressdb.sql" % env)
    get('/tmp/demisaucedb.sql', '%s/demisaucedb.sql' % PROJECT_ROOT)
    #get('/tmp/wordpressdb.sql', '%s/wordpressdb.sql' % PROJECT_ROOT)
    sudo("rm /tmp/*.sql")

def build(mysql_root_pwd=None,mysql_user_pwd=None,host=None,local=False):
    if mysql_root_pwd:
        env.mysql_root_pwd = mysql_root_pwd
    if mysql_user_pwd:
        env.mysql_user_pwd = mysql_user_pwd
    if host:
        env.host = host
    print("====== starting build:  env=%s" % env)
    sudo("apt-get -y install rsync")
    sudo("mkdir -p /vol; chown -R %s:%s /vol" % (env.user,env.user))
    sudo("chmod -R 770 /vol")
    sudo("usermod -a -G www-data ubuntu; usermod -a -G www-data demisauce")
    push_recipes() # do this first to force rsynch/ssh pwd at beginning to it doesn't 255 error timeout
    add_sources()
    _linux_base()
    _gearman()
    _memcached()
    _postfix()# must be installed before zamanda which installs it in interactive mode
    _mysql()
    #_zamanda()
    _nginx()
    _demisauce_pre_reqs()
    _redis_install()
    _redis_conf_update()
    _supervisord_install()
    _install_solr()
    _install_solr_war('dssolr')
    _solr_spatial()
    # move from temp home to /etc
    sudo("rsync  -pthrvz  /home/demisauce/src/demisauce/install/recipes/etc /") 
    #supervisor_update() # also starts supervisord
    sudo('/etc/init.d/tomcat6 restart')
    sudo('/etc/init.d/supervisord restart')
    sudo('/etc/init.d/memcached start')
    sudo('sudo update-rc.d supervisord defaults')

def all(mysql_root_pwd=None,mysql_user_pwd=None):
    """Build AND Release"""
    build(mysql_root_pwd=mysql_root_pwd,mysql_user_pwd=mysql_user_pwd)
    release(mysql_user_pwd=mysql_user_pwd)
    restart_web()

def build_solr(name='dssolr',host=None):
    """Build a solr server"""
    sudo("apt-get -y install rsync")
    if host:
        env.host = host
    print("====== starting build:  env=%s" % env)
    push_recipes() # do this first to force rsynch/ssh pwd at beginning to it doesn't 255 error timeout
    
    add_sources()
    _linux_base()
    _install_solr()
    _install_solr_war(name)
    _solr_spatial()
    sudo("/etc/init.d/tomcat6 restart")

def build_dev():
    "build dev linux machine with dependencies"
    sudo("apt-get -y install rsync")
    add_sources()
    _linux_base()
    _demisauce_pre_reqs()
    

def solr_conf():
    """Configuration Sync"""
    rsync_project('/vol/',local_dir='%(local_path)s/install/recipes/vol/' % env)
    sudo("rsync  -pthrvz  /vol/solr/conf /usr/local/tomcat6/dssolr/")
    sudo("/etc/init.d/tomcat6 restart")

def build_ec2():
    env.user = 'ubuntu'
    #http://www.barregren.se/blog/how-install-ubuntu-amazon-ec2
    #http://www.equivalence.co.uk/archives/1521
    # USE boto local('bin/ec2-create-volume -z %s -s 10' % (env.ec2zone))
    #thread.thread.sleep(30)
    #local('%s/.ec2/bin/ec2-attach-volume -d /dev/sdh -i %s %s' % (USER_HOME,env.ec2instance,env.ec2volume))
    sudo("useradd -d /home/demisauce -m demisauce")
    sudo("usermod -a -G admin demisauce; usermod -a -G demisauce ubuntu; usermod -a -G ubuntu demisauce")
    run("""
    export DEBIAN_FRONTEND=noninteractive
    echo "deb http://ppa.launchpad.net/ubuntu-on-ec2/ec2-tools/ubuntu karmic main" |
      sudo tee /etc/apt/sources.list.d/ubuntu-on-ec2-ec2-tools.list &&
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 9EE6D873 &&
    sudo apt-get update &&
    sudo -E apt-get upgrade -y &&
    sudo apt-get install -y xfsprogs &&
    sudo -E apt-get install -y \
      python-vm-builder ec2-ami-tools ec2-api-tools bzr &&
    bzr branch lp:vmbuilder
    codename=$(lsb_release -cs)
    echo "deb http://ppa.launchpad.net/alestic/ppa/ubuntu $codename main"|
      sudo tee /etc/apt/sources.list.d/alestic-ppa.list    
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys BE09C571
    sudo apt-get update && 
    sudo apt-get install -y ec2-consistent-snapshot &&
    sudo PERL_MM_USE_DEFAULT=1 cpan Net::Amazon::EC2
    """)
    #time.sleep(60)
    sudo("mkfs.xfs /dev/sdh")
    sudo('sudo su; echo "/dev/sdh /vol xfs noatime 0 0" >> /etc/fstab')
    sudo('mkdir /vol; mount /vol')

def bundle_ec2(access_key_id, secret_access_key):
    'first, start instance'
    # lets get your amazon keypair up onto the instance: 
    #os.system("scp -i ~/.ec2/id_rsa-%s ~/.ec2/{cert,pk}-*.pem root@%s:/mnt/" % (KEY_PAIR,instance_info.dnsName))
    put('~/.ec2/id_rsa-%s ~/.ec2/{cert,pk}-*.pem', '/tmp/')
    # move up the demisauce install file
    #os.system("scp -i ~/.ec2/id_rsa-%s %s root@%s:/mnt/" % (KEY_PAIR,DS_INSTALL_FILE,instance_info.dnsName))
    #put("scp -i ~/.ec2/id_rsa-%s %s root@%s:/mnt/" % (KEY_PAIR,DS_INSTALL_FILE,instance_info.dnsName))
    # ssh command
    ssh_cmd = 'ssh -i %sid_rsa-%s root@%s' % (DOT_EC2,KEY_PAIR,instance_info.dnsName)
    """Run these commands on your local machine
    ~/.ec2/bin/ec2-create-volume -z us-east-1a -s 10
    ~/.ec2/bin/ec2-describe-volumes vol-VVVV1111
    ec2-attach-volume -d /dev/sdh -i i-IIII1111 vol-VVVV1111
    """


