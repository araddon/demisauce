#!/usr/bin/env python
import logging
import json
import urllib
from formencode import Invalid, validators
from formencode.validators import *
import formencode
from tornado.options import options
from demisauce.controllers import NeedsadminController, RestMixin
from demisauce import model
from demisauce.model import meta
from demisauce.model import mapping
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.email import Email
from gearman.task import Task

log = logging.getLogger(__name__)


class AdminController(RestMixin, NeedsadminController):
    
    def index(self,id=0):
        if self.user and self.user.issysadmin:
            items = meta.DBSession.query(Site).all()
            self.render('site/site.html',items=items)
        else:
            return self.view(self.user.site_id)
    
    def enablesite(self,id=0):
        if not self.user or not self.user.issysadmin:
            # Get Out Of Here
            return self.redirect("/")
        
        if 'siteid' in self.request.arguments:
            site = meta.DBSession.query(Site).get(self.get_argument("siteid"))
            if site:
                user = meta.DBSession.query(Person).filter_by(email=site.email).first()
                if user:
                    url = '%s/account/site_signup?invitecode=%s&return_url=%s' % \
                        (options.base_url,
                            user.user_uniqueid,
                            urllib.quote_plus('/account/viewh/%s' % (user.hashedemail)))
                    json_dict = {
                        'emails':[user.email],
                        'template_name':'welcome_to_demisauce',
                        'template_data':{
                            'link':url,
                            'displayname':user.displayname,
                            'email':user.email
                        }
                    }
                    self.db.gearman_client.do_task(Task("email_send",json.dumps(json_dict), background=True))
                    site.enabled = True
                    site.save()
                return self.write('Enabled Site')
            
        return self.write('whoops, that didn\'t work')
    

_controllers = [
    (r"/admin/(.*?)/(.*?)", AdminController),
    (r"/admin/(.*?)", AdminController),
]