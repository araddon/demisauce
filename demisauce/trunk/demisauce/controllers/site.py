#!/usr/bin/env python
import logging
import urllib
from formencode import Invalid, validators
from formencode.validators import *
import formencode

from demisauce.controllers import RestMixin, BaseHandler, requires_admin
from demisauce import model
from demisauce.model import meta
from demisauce.model import mapping
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.email import Email

log = logging.getLogger(__name__)


class SiteValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(validators.Email(resolve_domain=False),
                           validators.String(not_empty=True))

class SiteController(RestMixin,BaseHandler):
    
    def index(self,id=0):
        return self.view(self.user.site_id)
    
    def view(self,id = 0):
        id = int(id) if id is not None else 0
        if id > 0 and (self.user is not None) and self.user.issysadmin:
            item = Site.saget(id)
        elif id is None or id == 0 and self.user:
            item = Site.get(-1,self.user.site_id)
        else:
            item = Site.get(-1,id)
            if not item.public:
                item = None
        self.render('/site/site.html',item=item)
    
    @requires_admin
    def cmntconfig(self):
        item = Site.get(-1,self.user.site_id)
        self.render('/site/comment.html',item=item)
    
    @requires_admin
    def help(self,id = 0):
        if id > 0:
            c.item = Site.get(-1,id)
            c.base_url = config['demisauce.url']
        else:
            c.item = Site.get(-1,self.user.site_id)
        self.render('/help/help.html')
    
    @requires_admin
    #@rest.dispatch_on(POST="edit_POST")
    def edit(self,id = 0):
        id = int(id)
        if id > 0 and self.user.isadmin and self.user.site_id == id:
            item = meta.DBSession.query(Site).get(id)
        elif id > 0 and self.user.issysadmin:
            item = meta.DBSession.query(Site).get(id)
        self.render('/site/site_edit.html',item=item)
    
    @requires_admin
    #@validate(schema=SiteValidation(), form='edit')
    def edit_POST(self,id = 0):
        """
        User has selected to change site config info
        """
        if 'objectid' in request.params:
            site = Site.get(-1,request.params['objectid'])
            
            if site is None:
                self.add_error("We experienced an error, please try again")
                
            else:
                site.name = self.form_result['name']
                site.description = self.form_result['description']
                site.email = self.form_result['email']
                site.slug = self.form_result['real_permalink']
                # TODO, check uniqueness
                site.public = bool(self.form_result['public'])
                site.base_url = self.form_result['base_url']
                site.site_url = self.form_result['site_url']
                site.save()
                
                # refresh session store
                user = Person.get(self.user.site_id,self.user.id)
                self.set_current_user(user)
                self.add_alert("Site settings were updated")
                
            
        else:
            self.add_error("There was an Error")
        
        return redirect('/site/view')
    


_controllers = [
    (r"/site/(.*?)/(.*?)", SiteController),
]
