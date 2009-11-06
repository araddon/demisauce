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
from demisauce import fixture
from demisauce import model
from demisauce.model import mapping
from demisauce.model import cms, email, site, person, \
    comment, meta, poll, service, tag, help

from paste.deploy import appconfig
from paste.script import command
from pylons import config

from demisauce.config.environment import load_environment

log = logging.getLogger(__name__)

class ChangeBaseSite(command.Command):
    """
    This is run from the command line like this::
    
        paster updatesite -p admin_password -e admin_email -h http://yoursite.com -i production.ini
    
    It updates the base admin site
    """
    max_args = 4
    min_args = 0
    usage = "updatesite"
    summary = "Updates data for base admin site"
    group_name = "demisauce"
    parser = command.Command.standard_parser(verbose=True)
    parser.add_option('--ini','-i',
                      dest='cfgfile',
                      default='library_test.ini',
                      help="Enter the ini file to load")
    parser.add_option('--password','-p',
                      dest='adminpwd',
                      default='admin',
                      help="Enter a password for Admin user [default user = sysadmin@demisauce.org, pwd = admin]")
    parser.add_option('--adminemail','-e',
                    dest='adminemail',
                    default='sysadmin@demisauce.org',
                    help="Enter the email of admin user [default = sysadmin@demisauce.org]")
    parser.add_option('--site','-s',
                    dest='site',
                    default='http://localhost:4950',
                    help="Enter the host address of new site [default = http://localhost:4950]")
    
    def command(self):
        print('new email = %s, new pwd = %s, new host = %s' % (self.options.adminpwd, 
            self.options.adminemail,self.options.site))
        conf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ini_file = os.path.join(conf_dir, self.options.cfgfile)
        conf = appconfig('config:' + ini_file)
        load_environment(conf.global_conf, conf.local_conf)
        s = meta.DBSession.query(site.Site).filter_by(id=1).first()
        s.email = self.options.adminemail
        s.base_url = self.options.site
        s.save()
        p = meta.DBSession.query(person.Person).filter_by(id=1).first()
        p.set_password(self.options.adminpwd)
        p.email = self.options.adminemail
        p.save()

class SetupTestData(command.Command):
    """
    This is run from the command line like this::
    
        paster dataload -i development.ini -c person
    
    It installs test data used by the libraries for testing
    """
    max_args = 2
    min_args = 0
    usage = "dataload"
    summary = "Installs test data into test.ini or ini file of choice"
    group_name = "demisauce"
    parser = command.Command.standard_parser(verbose=True)
    parser.add_option('--ini','-i',
                      dest='cfgfile',
                      default='library_test.ini',
                      help="Enter the config file to load")
    parser.add_option('--classtype','-c',
                    dest='classtype',
                    default='site.Site',
                    help="Enter the name of the class (assumed to be in demisauce.model.class.Class)")
    
    def command(self):
        conf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ini_file = os.path.join(conf_dir, self.options.cfgfile)
        conf = appconfig('config:' + ini_file)
        load_environment(conf.global_conf, conf.local_conf)
        if self.options.classtype:
            create_data_new(self.options.classtype,drop=True)
        else:
            create_data(ini_file)
    

def create_data_new(classtype,drop=False):
    models = None
    if classtype in dir(fixture):
        json_list = getattr(fixture, classtype)
        #print json_list
        models = model.ModelBase.from_json(json_list)
    if classtype == 'site' and drop:
        site.site_table.drop(checkfirst=True,bind=meta.engine)
        site.site_table.create(checkfirst=True,bind=meta.engine)
    elif classtype == 'person' and drop:
        person.person_table.drop(checkfirst=True,bind=meta.engine)
        person.person_table.create(checkfirst=True,bind=meta.engine)
        [m.after_load() for m in models]
    elif classtype == 'email' and drop:
        email.email_table.drop(checkfirst=True,bind=meta.engine)
        email.email_table.create(checkfirst=True,bind=meta.engine)
        [m.after_load() for m in models]
    elif classtype == 'comment' and drop:
        comment.comment_table.drop(checkfirst=True,bind=meta.engine)
        comment.comment_table.create(checkfirst=True,bind=meta.engine)
    elif classtype == 'poll' and drop:
        poll.poll_table.drop(checkfirst=True,bind=meta.engine)
        poll.question_table.drop(checkfirst=True,bind=meta.engine)
        poll.question_option_table.drop(checkfirst=True,bind=meta.engine)
        poll.poll_response_table.drop(checkfirst=True,bind=meta.engine)
        poll.answer_table.drop(checkfirst=True,bind=meta.engine)
        
        poll.poll_table.create(checkfirst=True,bind=meta.engine)
        poll.question_table.create(checkfirst=True,bind=meta.engine)
        poll.question_option_table.create(checkfirst=True,bind=meta.engine)
        poll.poll_response_table.create(checkfirst=True,bind=meta.engine)
        poll.answer_table.create(checkfirst=True,bind=meta.engine)
        for m in models:
            questions = model.ModelBase.from_json(fixture.poll_question)
            options = model.ModelBase.from_json(fixture.poll_question_option)
            for q in questions:
                m.questions.append(q)
                for o in options:
                    q.options.append(o)
    elif (classtype == 'app') and drop:
        service.app_table.drop(checkfirst=True,bind=meta.engine)
        service.service_table.drop(checkfirst=True,bind=meta.engine)
        service.app_table.create(checkfirst=True,bind=meta.engine)
        service.service_table.create(checkfirst=True,bind=meta.engine)
        json_list = getattr(fixture, 'service')
        models.extend(model.ModelBase.from_json(json_list))
    elif classtype == 'tag' and drop:
        tag.tag_table.drop(checkfirst=True,bind=meta.engine)
        tag.tag_map_table.drop(checkfirst=True,bind=meta.engine)
        tag.tag_table.create(checkfirst=True,bind=meta.engine)
        tag.tag_map_table.create(checkfirst=True,bind=meta.engine)
        
    if models:
        for m in models:
            #print m.to_json()
            m.save()
    else:
        print 'no class'

def create_fixture_data(classtype):
    models = None
    if classtype in dir(fixture):
        json_list = getattr(fixture, classtype)
        #print json_list
        models = model.ModelBase.from_json(json_list)
    if classtype == 'person':
        [m.after_load() for m in models]
    elif classtype == 'email':
        [m.after_load() for m in models]
    elif classtype == 'poll':
        for m in models:
            questions = model.ModelBase.from_json(fixture.poll_question)
            options = model.ModelBase.from_json(fixture.poll_question_option)
            for q in questions:
                m.questions.append(q)
                for o in options:
                    q.options.append(o)
    elif (classtype == 'app'):
        json_list = getattr(fixture, 'service')
        models.extend(model.ModelBase.from_json(json_list))
    
    if models:
        for m in models:
            #print m.to_json()
            m.save()
    else:
        print 'no class'


def create_data(ini_file):
    """
    Creates initial data
    """
    conf = appconfig('config:' + ini_file)
    load_environment(conf.global_conf, conf.local_conf)
    if 'test.ini' in ini_file:
        print 'dropping tables for testing:  %s' % ini_file
        meta.metadata.drop_all(bind=config['pylons.g'].sa_engine)
    print "Creating DB Tables if they dont exist"
    meta.metadata.create_all(bind=config['pylons.g'].sa_engine)
    s = meta.DBSession.query(site.Site).get(1)
    key = conf['demisauce.apikey']
    if not s:
        create_fixture_data('site')
        s = meta.DBSession.query(site.Site).get(1)
    
    if s.key != key:
        print 'Update %s demisauce.apikey to %s \n'  % (ini_file,s.key)  
    
    user = meta.DBSession.query(person.Person).filter_by(site_id=s.id,id=1).first()
    if not user:
        # pwd = raw_input('Enter the Password for admin: ')
        create_fixture_data('person')
        user = person.Person.get(1,1)
    
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
        
    create_fixture_data('comment')
    create_fixture_data('poll')
    create_fixture_data('email')
    create_fixture_data('app')
    create_fixture_data('tag')

    
def setup_config(command, filename, section, vars):
    """
    This is run from the command line like this:
    
    paster setup-app test.ini
    
    """
    print 'running setup_config %s, file=%s' % (command,filename)
    create_data(filename)

