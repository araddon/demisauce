#!/usr/bin/env python
"""
Setup the demisauce application

Example usage::

    # initial data setup, or data import from json seed file
    python manage.py --config=dev.conf --action=create_data --logging=debug \
        --seed_data_file=your_file.json
    
    # change base site info
    manage.py --action=updatesite \
        --adminpwd=admin_password \
        --adminemail=email@email.com \
        --base_url=http://ds.yourdomain.com
"""
import logging, sys, os, json
import tornado
from tornado.options import options, define
import app
from demisauce import model
from demisauce.model import meta
from demisauce.model import email, site, user, service, tag

log = logging.getLogger('demisauce')

define("action", default=None, help="Action to perform, [updatesite,create_data]")
define("adminpwd", default="admin",
        help="Enter a password for Admin user [default email = sysadmin@demisauce.org, pwd = admin]")
define('adminemail', 
        default='sysadmin@demisauce.org',
        help="Enter the email of admin user [default = sysadmin@demisauce.org]")
define('new_url', 
        default='http://localhost:4950',
        help="Enter the host address of new url [default = http://localhost:4950]")
define('seed_data_file', 
        default='db/seed_data.json',
        help="Enter the path to seed_data json file")

def print_help():
    print(__doc__)

def updatesite(app):
    """
    Updates the admin site user email, pwd, url::
    
        manage.py --action=updatesite \
            --adminpwd=admin_password \
            --adminemail=email@email.com \
            --new_url=http://ds.yourdomain.com
    
    It updates the base admin site
    """
    log.debug('new email = %s, new pwd = %s, new host = %s' % (options.adminpwd, 
        options.adminemail,options.site))
    s = app.db.session.query(site.Site).filter_by(id=1).first()
    s.email = options.adminemail
    s.base_url = options.site
    s.save()
    log.debug("Updates site, %s" % s)
    p = app.db.session.query(user.Person).filter_by(id=1).first()
    p.set_password(options.adminpwd)
    p.email = options.adminemail
    p.save()

def create_fixture_data(classtype,seed_data):
    models = None
    items = []
    jsondata = seed_data[classtype]
    from demisaucepy import Service, Email, DSUser, Site, App
    service_handle = {'site':Site,
                        'service':Service,
                        'person':DSUser,
                        'email':Email,
                        'app':App}
    svc_class = service_handle[classtype]
    if svc_class:
        for json_row in jsondata:
            id = 0
            if 'site_id' in json_row and json_row['site_id'] != 1:
                apikey = None
                for site_data in seed_data['site']:
                    if site_data['id'] == json_row['site_id']:
                        apikey = site_data['key']
                svc = svc_class(json_row,apikey=apikey)
            else:
                svc = svc_class(json_row)
            if 'id' in json_row:
                id = json_row['id']
            svc.POST(id)
    else:
        print 'no class for %s' % classtype


def create_data(app,drop_tables=False):
    """
    Creates initial seed data
    """
    if drop_tables:
        print 'dropping tables for testing' 
        app.db.metadata.drop_all(bind=app.db.engine)
    print "Creating DB Tables if they dont exist"
    app.db.metadata.create_all(bind=app.db.engine)
    seed_file = os.path.realpath(options.seed_data_file)
    json_file = open(seed_file)
    seed_data = json.loads(json_file.read())
    s = app.db.session.query(site.Site).get(1)
    if not s:
        print("no Base Site, create one")
        s = site.Site(name="demisauce", 
                key         = options.demisauce_api_key, 
                email       ="sysadmin@demisauce.org", 
                base_url    = options.demisauce_url,
                slug        = "demisauce",
                enabled     = True,
                is_sysadmin = True,
                description = "This is to your local app non hosted version of demisauce"
            )
        s.save()
        s = app.db.session.query(site.Site).get(1)
    
    create_fixture_data('site',seed_data)
    create_fixture_data('person',seed_data)
    create_fixture_data('email',seed_data)
    create_fixture_data('app',seed_data)
    create_fixture_data('service',seed_data)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    from demisaucepy import cache_setup
    cache_setup.load_cache()
    application = app.Application()
    if options.action == 'updatesite':
        log.debug("In data setup")
        updatesite(application)
    elif options.action == 'create_data':
        log.debug("in create_data call")
        create_data(application)
    elif options.action == 'test':
        json_string = fixture.service
        jsondata = json.loads(json_string)
        items = []
        for servicedata in jsondata:
            service = model.service.Service().from_dict(servicedata)
            items.append(service)
    else:
        print_help()
        tornado.options.parse_command_line([0,"--help"])

