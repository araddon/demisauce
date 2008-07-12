#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta
from demisauce.model import mapping
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.email import Email

log = logging.getLogger(__name__)


class AdminController(NeedsadminController):
    
    def index(self):
        if c.user and c.user.issysadmin:
            c.items = meta.DBSession.query(Site).all()
            return render('/site/site.html')
        else:
            return self.view(c.user.site_id)
    
    def enablesite(self,id=0):
        if not c.user.issysadmin:
            # Get Out Of Here
            return redirect_to(h.url_for(controller='home',action='index'))
            
        if 'siteid' in request.params and c.user and c.user.issysadmin:
            site = meta.DBSession.query(Site).get(request.params['siteid'])
            if site:
                site.enabled = True
                site.save()
                
                #TODO:  refactor out email send, do event observer type
                # now send email to user to create pwd etc
                user = meta.DBSession.query(Person).filter_by(email=site.email).first()
                if user:
                    url2 = urllib.quote_plus('/account/viewh/%s' % (user.hashedemail))
                    delay = 4
                    from demisauce.lib import scheduler
                    dnew = {}
                    dnew['link'] = '%s/account/site_signup?invitecode=%s&return_url=%s' %\
                        (base_url(),user.user_uniqueid,url2)
                    dnew['displayname'] = user.displayname
                    dnew['email'] = user.email
                    dnew['title'] = 'welcome'
                    scheduler.add_interval_task(send_emails,0,('welcome_to_demisauce',[user.email],dnew) , initialdelay=delay)
                
                return 'Enabled Site'
            
        return 'whoops, that didn\'t work'
    

