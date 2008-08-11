#!/usr/bin/env python
import logging
import urllib
from pylons import config
from formencode import Invalid, validators
from formencode.validators import *
import formencode

from demisauce.lib.base import *
from demisauce import model
from demisauce.model import meta, mapping
from demisauce.model.person import Person
from demisauce.model.site import Site
from demisauce.model.email import Email
from demisauce.model.help import Help, HelpResponse, helpstatus

log = logging.getLogger(__name__)

class HelpProcessFormValidation(formencode.Schema):
    """Form validation for the comment web admin"""
    allow_extra_fields = True
    filter_extra_fields = False
    title = formencode.All(String(not_empty=True))
    response = formencode.All(String(not_empty=True))

class HelpadminController(SecureController):
    def index(self):
        return self.viewlist()
    
    def viewlist(self,id=0):
        c.item = None
        filter = 'new'
        if 'filter' in request.params:
            filter = request.params['filter']
        
        if filter in helpstatus:
            c.helptickets = Help.by_site(c.user.site_id,20,filter)
        elif filter == 'recent':
            c.helptickets = Help.recent(c.user.site_id,20)
        
        if (id == 0 or id == None) and c.helptickets:
            if c.helptickets.count() > 0:
                c.item = c.helptickets[0]
        elif id > 0:
            c.item = Help.get(c.user.site_id,id)
            

        
        return render('/help/help_process.html')
    
    @rest.dispatch_on(POST="help_process_submit")
    def process(self,id=0):
        return self.viewlist(id)
    
    @validate(schema=HelpProcessFormValidation(), form='process')
    def help_process_submit(self,id=''):
        h = Help.get(c.user.site_id,int(self.form_result['help_id']))
        if h:
            item = HelpResponse(h.id,c.user)
            item.status = int(self.form_result['status'])
            item.response = sanitize(self.form_result['response'])
            item.title = sanitize(self.form_result['title'])
            if 'publish' in self.form_result:
                item.publish = int(self.form_result['publish'])
            item.url = h.url
            item.save()
            h.status = item.status
            h.save()
            return self.viewlist()
        else:
            #TODO panic?
            log.error('help_process_submit h not found: help_id = %s ' % (self.form_result['help_id']))
        return
    
    def view(self,id=0):
        c.item = Help.get(c.user.site_id,id)
        return render('/help/help_viewone.html')
    
