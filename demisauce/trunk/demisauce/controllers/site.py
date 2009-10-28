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


class SiteValidation(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = False
    email = formencode.All(validators.Email(resolve_domain=False),
                           validators.String(not_empty=True))

class SiteController(BaseController):
    
    def index(self):
        return self.view(c.user.site_id)
    
    def view(self,id = 0):
        id = int(id) if id not None else 0
        if id > 0 and (c.user is not None) and c.user.issysadmin:
            c.item = Site.saget(id)
        elif id is None or id == 0 and c.user:
            c.item = Site.get(-1,c.user.site_id)
        else:
            c.item = Site.get(-1,id)
            if not c.item.public:
                c.item = None
        return render('/site/site.html')
    
    @requires_role('admin')
    def cmntconfig(self):
        c.item = Site.get(-1,c.user.site_id)
        return render('/site/comment.html')
    
    @requires_role('admin')
    def help(self,id = 0):
        if id > 0:
            c.item = Site.get(-1,id)
            c.base_url = config['demisauce.url']
        else:
            c.item = Site.get(-1,c.user.site_id)
        return render('/help/help.html')
    
    @requires_role('admin')
    @rest.dispatch_on(POST="edit_POST")
    def edit(self,id = 0):
        id = int(id)
        if id > 0 and c.user.isadmin and c.user.site_id == id:
            c.item = meta.DBSession.query(Site).get(id)
        elif id > 0 and c.user.issysadmin:
            c.item = meta.DBSession.query(Site).get(id)
        c.base_url = config['demisauce.url']
        return render('/site/site_edit.html')
    
    @requires_role('admin')
    @validate(schema=SiteValidation(), form='edit')
    def edit_POST(self,id = 0):
        """
        User has selected to change site config info
        """
        if 'objectid' in request.params:
            site = Site.get(-1,request.params['objectid'])
            
            if site is None:
                h.add_error("We experienced an error, please try again")
                
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
                user = Person.get(c.user.site_id,c.user.id)
                self.start_session(user)
                h.add_alert("Site settings were updated")
                
            
        else:
            h.add_error("There was an Error")
        
        return redirect_wsave('/site/view')
    

