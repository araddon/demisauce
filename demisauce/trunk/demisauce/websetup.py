"""
Setup the demisauce application

Example usage::

    yourproj% paster setup-app development.ini
    Running setup_config() from demisauce.websetup
    Creating DB Tables
    Successfully Created DB Tables
    you need to update your ini file with the site key for some functionality
    demisauce.apikey = 299ebe6c0db5e3ab277918f5796cd00f7fdcb12d
    demisauce loginame = guest@demisauce.org
    demisauce password = guest
    found and updated demisauce.apikey to 299ebe6c0db5e3ab277918f5796cd00f7fdcb12d


"""
import logging
import ConfigParser
import sys, os

from paste.deploy import appconfig
from paste.script import command
from pylons import config

from demisauce.config.environment import load_environment

log = logging.getLogger(__name__)



class SetupTestData(command.Command):
    """
    This is run from the command line like this:
    
    paster testdata
    
    It installs test data used by the libraries for testing
    """
    max_args = 1
    min_args = 0
    usage = "testdata"
    summary = "Installs test data into test.ini or \
        ini file of choice"
    group_name = "demisauce"
    parser = command.Command.standard_parser(verbose=True)
    parser.add_option('--config','-c',
                      action='store_true',
                      dest='cfgfile',
                      default='library_test.ini',
                      help="Enter the config file to load")
    
    def command(self):
        if self.args and len(self.args) >= 0:
            self.options.cfgfile = self.args[0]
        conf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ini_file = os.path.join(conf_dir, self.options.cfgfile)
        create_data(ini_file)
    

def create_data(ini_file):
    """
    Creates initial data
    """
    conf = appconfig('config:' + ini_file)
    load_environment(conf.global_conf, conf.local_conf)
    from demisauce import model
    from demisauce.model import mapping
    from demisauce.model import cms, email, site, person, \
        comment, meta
    if 'test.ini' in ini_file:
        print 'dropping tables for testing:  %s' % ini_file
        meta.metadata.drop_all(bind=config['pylons.g'].sa_engine)
    print "Creating DB Tables if they dont exist"
    meta.metadata.create_all(bind=config['pylons.g'].sa_engine)
    s = meta.DBSession.query(site.Site).get(1)
    key = conf['demisauce.apikey']
    if not s:
        s = site.Site('Demisauce Sys Admin', 'guest@demisauce.org')
        s.description = 'this is Demisauce Site to support itself'
        s.enabled = True
        s.slug = 'demisauce.org'
        s.site_url = 'http://localhost:8080'
        if key:
            newkey = s.create_sitekey()
            print '\nWe used your existing ApiKey:   \n%s \nHowever, we \
strongly advise you to change it, \nwe generated you a new \
random one:\n%s, \nyou can enter it into your ini file:\n%s' % (key,newkey,ini_file)
            s.key = key
        s.save()
    
    if s.key != key:
        print 'Update %s demisauce.apikey to %s \n'  % (ini_file,s.key)  
    
    user = meta.DBSession.query(person.Person).filter_by(site_id=s.id,id=1).first()
    if not user:
        pwd = 'admin'
        user = person.Person(s.id, 'sysadmin@demisauce.org','Sys Admin @Demisauce',pwd)
        user.isadmin = True
        user.verified = True
        user.waitinglist = False
        user.issysadmin = True
        user.save()
        print  '\ndemisauce sysadmin username = %s' % user.email
        print 'password = %s\n' % pwd
    
    adminuser = meta.DBSession.query(person.Person).filter_by(site_id=s.id,email='admin@demisauce.org').first()
    if not adminuser:
        pwd = 'admin'
        adminuser = person.Person(s.id, 'admin@demisauce.org','Admin @Demisauce',pwd)
        adminuser.verified = True
        adminuser.waitinglist = False
        adminuser.isadmin = True
        adminuser.save()
        print  'demisauce site admin username = %s' % adminuser.email
        print 'password = %s\n' % pwd
    
    cmsitem = cms.Cmsitem.get_root(site_id=s.id)
    if not cmsitem:
        cmsitem = cms.Cmsitem(s.id, 'root','root, do not edit')
        cmsitem.item_type='root'
        from demisauce.fixturedata import cmsitems
        for item in cmsitems:
            cmstemp = cms.Cmsitem(s.id, item['title'],item['content'])
            if 'url' in item: cmstemp.url = item['url']
            cmsitem.addChild(cmstemp)
            if 'children' in item:
                cmstemp.item_type = 'folder'
                for citem in item['children']:
                    cmstemp2 = cms.Cmsitem(s.id, citem['title'],citem['content'])
                    if 'url' in citem: cmstemp2.url = citem['url']
                    rid = cmstemp.rid and (cmstemp.rid + '/') or ''
                    cmstemp2.rid = ('%s%s' % (rid,cmstemp2.key)).lower()
                    cmstemp.addChild(cmstemp2)
        
        cmsitem.save()
        print 'created items   '
        
    cmt = comment.Comment(s.id)
    cmt.set_user_info(user)
    cmt.uri = '/our/foo/bar/1'
    cmt.comment = 'this is a comment'
    cmt.save()
    
    
    emailitem = meta.DBSession.query(email.Email).filter_by(site_id=s.id,
        subject='Thank You for registering with Demisauce').first()
    if not emailitem:
        emailitem = email.Email(s.id, 'Thank You for registering with Demisauce')
        emailitem.template = """Welcome to Demisauce, we are are currently allowing a few users to try out our hosted service, and will send you an invite when we can accept more testers.  However, this is also an open source project so please feel free to download and try it out yourself.  

More info at http://www.demisauce.org 
or at:   http://demisauce.googlecode.com

Your Email address $email will not be used other than for logging in.

Thank You

The Demisauce Team
        """
        emailitem.from_name = 'Demisauce Web'
        emailitem.from_email = 'guest@demisauce.org'
        emailitem.to = ''
        emailitem.save()
        emailitem2 = email.Email(s.id,'Welcome To Demisauce')
        emailitem2.template = """Welcome to Demisauce, Your account has been enabled, and you can start using services on demisauce.
        
To verify your account you need to click and finish registering $link
        
Thank You
        
The Demisauce Team
        """
        emailitem2.from_name = 'Demisauce Admin'
        emailitem2.from_email = 'guest@demisauce.org'
        emailitem2.to = ''
        emailitem2.save()
        
        emailitem3 = email.Email(s.id,'Invitation to Demisauce')
        emailitem3.from_email = 'guest@demisauce.org'
        emailitem3.from_name = 'Demisauce Web'
        emailitem3.template = """Welcome to Demisauce, You have recieved an invite from $from , and an account has been created for you.

To verify your account you need to click and finish registering $link

Thank You

Demisauce Team"""
        emailitem3.save()
        
        email4 = email.Email(s.id,'Comment Notification')
        email4.key = 'comment-notification'
        email4.from_email = 'guest@demisauce.org'
        email4.from_name = 'Demisauce Web'
        email4.template = """Hello;

$email has Commented on your $sitename   on page $url

Thank You

Demisauce Team"""
        email4.save()

    
def setup_config(command, filename, section, vars):
    """
    This is run from the command line like this:
    
    paster setup-app test.ini
    
    """
    print 'running setup_config %s, file=%s' % (command,filename)
    create_data(filename)

