#!/usr/bin/env python
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
import sys, os
import tornado
from tornado.options import options, define
import app
try:
    # For Python < 2.6 or people using a newer version of simplejson
    import simplejson as json
except ImportError:
    # For Python >= 2.6
    import json
from demisauce import fixture
from demisauce import model
from demisauce.model import mapping
from demisauce.model import cms, email, site, person, \
    comment, meta, poll, service, tag, help

log = logging.getLogger(__name__)
define("action", default=None, help="Action to perform, [updatesite,create_data]")
define("adminpwd", default="admin",
        help="Enter a password for Admin user [default email = sysadmin@demisauce.org, pwd = admin]")
define('adminemail', 
        default='sysadmin@demisauce.org',
        help="Enter the email of admin user [default = sysadmin@demisauce.org]")
define('site', 
        default='http://localhost:4950',
        help="Enter the host address of new site [default = http://localhost:4950]")

def updatesite(app):
    """
    This is run from the command line like this::
    
        app.py -updatesite -p admin_password -e email@email.com
    
    It updates the base admin site
    """
    log.debug('new email = %s, new pwd = %s, new host = %s' % (options.adminpwd, 
        options.adminemail,options.site))
    s = app.db.session.query(site.Site).filter_by(id=1).first()
    s.email = options.adminemail
    s.base_url = options.site
    s.save()
    log.debug("Updates site, %s" % s)
    p = app.db.session.query(person.Person).filter_by(id=1).first()
    p.set_password(options.adminpwd)
    p.email = options.adminemail
    p.save()

def dataload(app):
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
    if hasattr(fixture,classtype):
        json_string = getattr(fixture, classtype)
        #log.debug("about to load site json_string: %s" % json_string)
        jsondata = json.loads(json_string)
    items = []
    if classtype == 'site':
        for sitedata in jsondata:
            logging.debug('create')
            site = model.site.Site().from_dict(sitedata)
            items.append(site)
    elif classtype == 'person':
        for persondata in jsondata:
            person = model.person.Person().from_dict(persondata)
            items.append(person)
        [m.after_load() for m in items]
    elif classtype == 'email':
        for emaildata in jsondata:
            email = model.email.Email().from_dict(emaildata)
            items.append(email)
        [m.after_load() for m in items]
    elif classtype == 'app':
        for appdata in jsondata:
            appitem = model.service.App().from_dict(appdata)
            items.append(appitem)
    elif classtype == 'service':
        for servicedata in jsondata:
            service = model.service.Service().from_dict(servicedata)
            items.append(service)
    if items:
        for m in items:
            #print m.to_json()
            m.save()
    else:
        print 'no class'


def create_data(app,ini_file = {}):
    """
    Creates initial data
    """
    if 'test.ini' in ini_file:
        print 'dropping tables for testing:  %s' % ini_file
        app.db.metadata.drop_all(bind=app.db.engine)
    print "Creating DB Tables if they dont exist"
    app.db.metadata.create_all(bind=app.db.engine)
    s = app.db.session.query(site.Site).get(1)
    if not s:
        print("no site, create one")
        create_fixture_data('site')
        s = app.db.session.query(site.Site).get(1)
    
    if s.key != options.demisauce_api_key:
        print 'Update %s demisauce.apikey to %s \n'  % (ini_file,s.key)  
    
    user = app.db.session.query(person.Person).filter_by(site_id=s.id,email="sysadmin@demisauce.org").first()
    if not user:
        # pwd = raw_input('Enter the Password for admin: ')
        log.debug("Creating persons?")
        create_fixture_data('person')
        user = person.Person.get(1,1)
    
    create_fixture_data('email')
    create_fixture_data('app')
    create_fixture_data('service')


def setup_config(command, filename, section, vars):
    """
    This is run from the command line like this:
    
    paster setup-app test.ini
    
    """
    print 'running setup_config %s, file=%s' % (command,filename)
    create_data(filename)



if __name__ == "__main__":
    tornado.options.parse_command_line()
    application = app.Application()
    if options.action == 'updatesite':
        logging.debug("In data setup")
        updatesite(application)
    elif options.action == 'create_data':
        log.debug("in create_data call")
        create_data(application)

